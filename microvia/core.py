"""Analytical copper balance and observed-data utilities. No tool control."""

import csv
import math
from datetime import datetime
from statistics import mean

FIELDS = (
    "lot",
    "sample",
    "timestamp",
    "source",
    "geometry",
    "diameter_um",
    "depth_um",
    "current_a_dm2",
    "time_min",
    "efficiency",
    "fill_ratio",
)


def gate(valid, evidence, in_range, same_lot):
    return all((valid, evidence, in_range, same_lot))


def number(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("nonfinite measurement")
    return result


def validate(rows):
    accepted, quarantined, seen, last = [], [], set(), {}
    for index, original in enumerate(rows):
        row = dict(original)
        try:
            if any(not str(row.get(f, "")).strip() for f in FIELDS):
                raise ValueError("missing required value")
            for f in FIELDS[5:]:
                row[f] = number(row[f])
            if any(row[f] <= 0 for f in FIELDS[5:9]):
                raise ValueError("nonpositive physical measurement")
            if not 0 < row["efficiency"] <= 1 or not 0 <= row["fill_ratio"] <= 1:
                raise ValueError("ratio outside [0,1]")
            at = datetime.fromisoformat(row["timestamp"])
            if at.tzinfo is None:
                raise ValueError("timestamp timezone required")
            identity = (row["lot"], row["sample"])
            if identity in seen:
                raise ValueError("duplicate lot/sample")
            if row["lot"] in last and at < last[row["lot"]]:
                raise ValueError("time reversal within lot")
            seen.add(identity)
            last[row["lot"]] = at
            accepted.append(row)
        except (ValueError, TypeError, OverflowError) as exc:
            quarantined.append({"row": index + 2, "reason": str(exc)})
    return {"accepted": accepted, "quarantined": quarantined}


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(FIELDS):
            raise ValueError("CSV columns must match documented unit-labelled schema")
        return validate(reader)


def copper_balance(current_a_dm2, time_min, efficiency, diameter_um, depth_um):
    j, t, eta, diameter, depth = map(
        number, (current_a_dm2, time_min, efficiency, diameter_um, depth_um)
    )
    if min(j, t, diameter, depth) <= 0 or not 0 < eta <= 1:
        raise ValueError("invalid physical parameters")
    # Faraday: h = j*t*M/(z*F*rho). A/dm2 -> A/m2; min -> s; m -> um.
    thickness = j * 100 * t * 60 * 0.063546 * eta / (2 * 96485.33212 * 8960) * 1e6
    volume = math.pi * (diameter / 2) ** 2 * depth
    return {
        "planar_equivalent_thickness_um": thickness,
        "cylindrical_void_volume_um3": volume,
        "ideal_bottom_only_fill_minutes": depth / thickness * t,
        "assumptions": [
            "uniform planar current density",
            "constant supplied efficiency",
            "cylindrical empty via",
            "bottom-only time is ideal, not a process prediction",
        ],
    }


def mask_metrics(mask, pixel_um):
    scale = number(pixel_um)
    if (
        scale <= 0
        or not mask
        or not mask[0]
        or any(len(r) != len(mask[0]) for r in mask)
    ):
        raise ValueError("positive calibration and rectangular nonempty mask required")
    if any(type(v) is not int or v not in (0, 1, 2) for r in mask for v in r):
        raise ValueError("mask labels: 0 outside, 1 deposited copper, 2 unfilled via")
    copper = sum(v == 1 for r in mask for v in r)
    void = sum(v == 2 for r in mask for v in r)
    if not copper + void:
        raise ValueError("empty via region")
    return {
        "area_fill_ratio": copper / (copper + void),
        "copper_area_um2": copper * scale**2,
        "unfilled_area_um2": void * scale**2,
        "definition": "2D section area fraction, not height filling ratio or 3D void volume",
    }


def analyze(validation):
    groups = {}
    for row in validation["accepted"]:
        identity = (row["lot"], row["geometry"], row["diameter_um"], row["depth_um"])
        groups.setdefault(identity, []).append(row)
    results = []
    for identity, rows in sorted(groups.items()):
        ordered = sorted(rows, key=lambda r: r["current_a_dm2"])
        split = len(ordered) // 2
        difference = None
        if split and len({r["current_a_dm2"] for r in rows}) > 1:
            difference = mean(r["fill_ratio"] for r in ordered[split:]) - mean(
                r["fill_ratio"] for r in ordered[:split]
            )
        results.append(
            {
                "lot": identity[0],
                "geometry": identity[1:],
                "n": len(rows),
                "mean_fill_ratio": mean(r["fill_ratio"] for r in rows),
                "higher_minus_lower_current_fill": difference,
                "interpretation": "association only; bath age, additives and agitation may confound",
                "next_check": "matched geometry and bath; randomize current order; replicate and inspect sections",
            }
        )
    return {
        "strata": results,
        "quarantined": validation["quarantined"],
        "factory_yield_effect": "not measured",
    }


def plan(validation, lot, geometry):
    rows = [
        r
        for r in validation["accepted"]
        if r["lot"] == lot and r["geometry"] == geometry
    ]
    same_shape = len({(r["diameter_um"], r["depth_um"]) for r in rows}) == 1
    allowed = gate(
        not validation["quarantined"], bool(rows), len(rows) >= 3, same_shape
    )
    if not allowed:
        return {
            "state": "abstain",
            "reason": "requires clean input and >=3 observations of one lot/geometry/shape",
        }
    low = min(r["current_a_dm2"] for r in rows)
    high = max(r["current_a_dm2"] for r in rows)
    if low == high:
        return {"state": "abstain", "reason": "no observed current range"}
    conditions = [low, (low + high) / 2, high]
    return {
        "state": "experimental_design_only",
        "lot": lot,
        "geometry": geometry,
        "current_a_dm2": conditions,
        "replicates_each": 3,
        "time_min_hold": mean(r["time_min"] for r in rows),
        "required_controls": [
            "bath composition and age measured and held constant",
            "same geometry, agitation and temperature",
            "randomized order",
        ],
        "reason": "bounded replicated contrast to test observed association; not a production recipe",
        "production_recommendation": "abstain: no validated bath-specific model",
    }
