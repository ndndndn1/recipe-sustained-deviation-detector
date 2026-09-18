"""Frozen v3 factorial evaluator; policies cannot access scenario functions."""

import json
import random
import time
from statistics import mean

from .benchmark import GRID
from .calibration import calibrate
from .policies import recommend, search
from .robust_benchmark import interval, truth

FAMILIES = (
    "smooth",
    "interaction",
    "narrow",
    "drift",
    "heteroscedastic",
    "bias",
    "late_shift",
    "infeasible",
)
CONTEXT = {
    "geometry": "synthetic",
    "bath_id": "simulation",
    "instrument": "oracle-pair",
    "quality_metric": "height_fill_ratio",
    "unit": "ratio",
}


def response(seed, family, p, step):
    q, t = truth(
        seed,
        family if family in ("smooth", "interaction", "narrow", "drift") else "smooth",
        p,
        step,
    )
    if family == "infeasible":
        q = min(q, 0.7)
    if family == "late_shift" and step >= 14:
        q = max(0, q - 0.2)
    return q, t


def measure(seed, family, p, step):
    q, t = response(seed, family, p, step)
    rng = random.Random(f"v3:{seed}:{family}:{p}:{step}")
    sd = 0.02 + 0.10 * p[0] if family == "heteroscedastic" else 0.04
    return q + rng.gauss(0, sd) + (0.1 if family == "bias" else 0), t + rng.gauss(0, 2)


def calibration_for(family):
    rows = []
    for i in range(40):
        p = random.Random(i + 91).choice(GRID)
        q, _ = response(-100, family, p, i % 14)
        observed, _ = measure(-100, family, p, i % 14)
        rows.append(
            {
                "measurement_id": f"cal-{i}",
                "replicate_group": str(p),
                "context": CONTEXT,
                "calibration_source": "synthetic independent oracle reference",
                "measured_at": f"2026-01-01T00:{i:02d}:00+00:00",
                "bath_age": 0,
                "temperature": 20,
                "agitation": 1,
                "observed": observed,
                "reference": q,
            }
        )
    return calibrate({"context": CONTEXT, "measurements": rows})


def trial(seed, family, strategy, policy, repeat=False):
    started = time.monotonic()
    history = []
    trace = []
    initial = random.Random(seed).sample(GRID, 8)
    remaining = [p for p in GRID if p not in initial]
    rng = random.Random(seed + 22)
    for step in range(20):
        if step < 8:
            p = initial[step]
        elif repeat and step >= 14:
            # Six additional measurements consumed, not free observations.
            p = history[step - 14][0]
        else:
            p = search(history, remaining, strategy, rng)
            remaining.remove(p)
        q, t = measure(seed, family, p, step)
        history.append((p, q, t))
        trace.append(
            {
                "step": step,
                "condition": p,
                "quality": q,
                "duration": t,
                "reason": "initial"
                if step < 8
                else "repeat"
                if repeat and step >= 14
                else strategy,
                "true_query_violation": response(seed, family, p, step)[0] < 0.8,
            }
        )
    c = calibration_for(family) if policy == "calibrated-margin" else None
    rec = recommend(history, policy, c, CONTEXT)
    feasible = [
        response(seed, family, p, 20)[1]
        for p in GRID
        if response(seed, family, p, 20)[0] >= 0.8
    ]
    abstain = rec["state"] == "abstain"
    violation = False
    loss = 1.0
    if not abstain:
        q, t = response(seed, family, rec["point"], 20)
        violation = q < 0.8
        if not violation and feasible:
            loss = max(0, (t - min(feasible)) / 120)
    return {
        "seed": seed,
        "family": family,
        "strategy": strategy,
        "policy": policy,
        "repeat": repeat,
        "loss": loss,
        "violation": violation,
        "abstention": abstain,
        "no_feasible": not feasible,
        "feasible_found": any(
            response(seed, family, p, 20)[0] >= 0.8 for p, _, _ in history
        ),
        "query_violation_rate": mean(r["true_query_violation"] for r in trace),
        "budget": len(trace),
        "seconds": time.monotonic() - started,
        "trace": trace,
        "recommendation": rec,
    }


def safe_trial(seed, family, strategy, policy, repeat=False):
    """Keep failed trials in the denominator and prohibit promotion on errors."""
    try:
        return trial(seed, family, strategy, policy, repeat)
    except Exception as exc:  # noqa: BLE001 - failed trials must remain in denominator
        return {
            "seed": seed,
            "family": family,
            "strategy": strategy,
            "policy": policy,
            "repeat": repeat,
            "loss": 1.0,
            "violation": True,
            "abstention": True,
            "feasible_found": False,
            "query_violation_rate": 1.0,
            "seconds": 0.0,
            "budget": 0,
            "trace": [],
            "error": type(exc).__name__,
        }


def run():
    # Full policy separation on development only; candidate frozen before unseen test.
    configs = [
        (s, p, r)
        for s in ("uniform", "random", "adaptive", "conservative")
        for p in ("raw", "fixed-margin", "calibrated-margin")
        for r in (False, True)
    ]
    development = []
    for cfg in configs:
        rows = [safe_trial(seed, f, *cfg) for seed in range(10) for f in FAMILIES]
        development.append(
            {
                "config": cfg,
                "loss": mean(r["loss"] for r in rows),
                "errors": sum("error" in r for r in rows),
            }
        )
    baseline = min(
        (r for r in development if r["config"][0] == "uniform"), key=lambda r: r["loss"]
    )["config"]
    candidate = min(
        (r for r in development if r["config"][0] != "uniform"), key=lambda r: r["loss"]
    )["config"]
    test = []
    for seed in range(1000, 1100):
        for f in FAMILIES:
            for name, cfg in [("baseline", baseline), ("candidate", candidate)]:
                row = safe_trial(seed, f, *cfg)
                row["arm"] = name
                test.append(row)
    summary = {
        name: {
            k: mean(r[k] for r in test if r["arm"] == name)
            for k in (
                "loss",
                "violation",
                "abstention",
                "feasible_found",
                "query_violation_rate",
                "seconds",
            )
        }
        for name in ("baseline", "candidate")
    }
    gains = [
        mean(r["loss"] for r in test if r["seed"] == s and r["arm"] == "baseline")
        - mean(r["loss"] for r in test if r["seed"] == s and r["arm"] == "candidate")
        for s in range(1000, 1100)
    ]
    ci = interval(gains)
    errors = sum("error" in r for r in test) + sum(r["errors"] for r in development)
    passed = (
        errors == 0
        and ci[0] > 0
        and summary["candidate"]["loss"] <= 0.9 * summary["baseline"]["loss"]
        and summary["candidate"]["violation"] <= summary["baseline"]["violation"]
    )
    return {
        "version": 3,
        "development": development,
        "baseline": baseline,
        "candidate": candidate,
        "summary": summary,
        "gain_ci95": ci,
        "promote": passed,
        "runs": test,
        "evaluation_errors": errors,
        "deployment": "research only; operational default remains bounded-design",
        "calibration_cost": "40 independent synthetic reference pairs per family, external to 20-query budget; same availability across arms",
        "per_family": {
            f: {
                name: mean(
                    r["loss"] for r in test if r["family"] == f and r["arm"] == name
                )
                for name in ("baseline", "candidate")
            }
            for f in FAMILIES
        },
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
