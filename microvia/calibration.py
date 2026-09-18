"""One-sided paired reference residual calibration; no implicit reference values."""

import math
from datetime import datetime

CONTEXT = ("geometry", "bath_id", "instrument", "quality_metric", "unit")


def calibrate(data):
    context = data.get("context", {})
    if any(
        not isinstance(context.get(k), str) or not context[k].strip() for k in CONTEXT
    ):
        raise ValueError("complete measurement context required")
    if context["unit"] != "ratio" or context["quality_metric"] != "height_fill_ratio":
        raise ValueError("only ratio height_fill_ratio calibration is supported")
    rows = data.get("measurements", [])
    seen = set()
    residuals = []
    times = []
    for row in rows:
        identity = row["measurement_id"]
        if not identity or identity in seen:
            raise ValueError("duplicate or missing measurement_id")
        seen.add(identity)
        if row.get("context") != context:
            raise ValueError("mixed calibration context")
        if not row.get("calibration_source") or not row.get("replicate_group"):
            raise ValueError("reference source and replicate group required")
        at = datetime.fromisoformat(row["measured_at"])
        if at.tzinfo is None:
            raise ValueError("timezone required")
        times.append(at)
        for k in ("bath_age", "temperature", "agitation", "observed", "reference"):
            if not math.isfinite(float(row[k])):
                raise ValueError("nonfinite measurement")
        if not 0 <= row["reference"] <= 1:
            raise ValueError("reference outside [0,1]")
        residuals.append(row["observed"] - row["reference"])
    if len(rows) < 30:
        return {
            "state": "abstain",
            "reason": "at least 30 paired reference measurements required",
            "n": len(rows),
        }
    rank = min(len(rows), math.ceil((len(rows) + 1) * 0.95))
    return {
        "version": 1,
        "state": "calibrated",
        "context": context,
        "n": len(rows),
        "margin": max(0, sorted(residuals)[rank - 1]),
        "target_quantile": 0.95,
        "period": [min(times).isoformat(), max(times).isoformat()],
        "measurement_ids": sorted(seen),
        "controls": {
            k: [min(float(r[k]) for r in rows), max(float(r[k]) for r in rows)]
            for k in ("bath_age", "temperature", "agitation")
        },
        "validity": "empirical paired residual quantile; exchangeability unverified; no safety guarantee",
        "variance_components": "instrument repeatability and process variation not separately identified",
    }


def in_scope(calibration, data):
    if calibration.get("version") != 1 or calibration.get("n", 0) < 30:
        return False
    margin = calibration.get("margin")
    if not isinstance(margin, (float, int)) or not math.isfinite(margin) or margin < 0:
        return False
    if calibration.get("state") != "calibrated" or data.get(
        "context"
    ) != calibration.get("context"):
        return False
    if data.get("drift_detected") is not False:
        return False
    if set(calibration["measurement_ids"]) & {
        r["measurement_id"] for r in data["measurements"]
    }:
        return False
    for row in data["measurements"]:
        if row.get("context") != calibration["context"]:
            return False
        for k, (lo, hi) in calibration["controls"].items():
            v = float(row[k])
            if not math.isfinite(v) or not lo <= v <= hi:
                return False
    return True


def plan_measured(data, calibration, strategy, policy):
    import random

    from .policies import recommend, search

    rows = data.get("measurements", [])
    if len(rows) < 3:
        return {"state": "abstain", "reason": "insufficient observations"}
    ids = [r["measurement_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate measurement_id")
    if any(r.get("context") != data.get("context") for r in rows):
        raise ValueError("mixed context")
    context = data.get("context", {})
    if (
        any(not context.get(k) for k in CONTEXT)
        or context.get("unit") != "ratio"
        or context.get("quality_metric") != "height_fill_ratio"
    ):
        raise ValueError("complete supported measurement context required")
    history = []
    previous = None
    for r in rows:
        if (
            not r.get("measurement_id")
            or not r.get("replicate_group")
            or not r.get("calibration_source")
        ):
            raise ValueError(
                "measurement identity, replicate group and source required"
            )
        at = datetime.fromisoformat(r["measured_at"])
        if at.tzinfo is None or (previous is not None and at < previous):
            raise ValueError("timezone-aware ordered measurements required")
        previous = at
        for key in ("bath_age", "temperature", "agitation"):
            if not math.isfinite(float(r[key])):
                raise ValueError("nonfinite process control")
        p = tuple(float(v) for v in r["condition"])
        if len(p) != 2 or any(not math.isfinite(v) or not 0 <= v <= 1 for v in p):
            raise ValueError("normalized condition outside [0,1]")
        q, t = float(r["observed"]), float(r["duration"])
        if not math.isfinite(q) or not math.isfinite(t) or t <= 0:
            raise ValueError("invalid observed response")
        history.append((p, q, t))
    if policy == "calibrated-margin" and not in_scope(calibration or {}, data):
        return {
            "state": "abstain",
            "reason": "calibration scope, overlap or drift check failed",
        }
    result = recommend(history, policy, calibration, data.get("context"))
    remaining = [tuple(p) for p in data.get("candidate_conditions", [])]
    for p in remaining:
        if len(p) != 2 or any(
            not math.isfinite(v)
            or not min(h[0][i] for h in history) <= v <= max(h[0][i] for h in history)
            for i, v in enumerate(p)
        ):
            raise ValueError("candidate outside observed bounding box")
    result["next_experiment"] = (
        search(history, remaining, strategy, random.Random(0)) if remaining else None
    )
    result["experiment_note"] = (
        "bounding box is not proof of safety; manual process review required"
    )
    result["evidence_measurement_ids"] = ids
    return result
