"""Observation-only policies. No simulator import or hidden objective access."""

import math
from statistics import mean

from .benchmark import choose


def search(history, remaining, strategy, rng):
    if strategy == "random":
        return rng.choice(remaining)
    if strategy == "adaptive":
        return choose(history, remaining)
    if strategy == "uniform":
        return max(remaining, key=lambda p: min(math.dist(p, h[0]) for h in history))
    if strategy != "conservative":
        raise ValueError("unknown strategy")

    def score(p):
        near = sorted((math.dist(p, x), q, t) for x, q, t in history)[:4]
        return (
            mean(x[2] for x in near)
            + 300 * max(0, 0.8 - (mean(x[1] for x in near) - 0.08 - near[0][0] * 0.2))
            - 15 * near[0][0]
        )

    return min(remaining, key=score)


def recommend(history, policy, calibration=None, context=None):
    if policy not in ("raw", "fixed-margin", "calibrated-margin"):
        raise ValueError("unknown recommendation policy")
    margin = 0 if policy == "raw" else 0.08
    if policy == "calibrated-margin":
        if (
            not calibration
            or calibration.get("state") != "calibrated"
            or calibration.get("context") != context
        ):
            return {"state": "abstain", "reason": "missing or out-of-scope calibration"}
        margin = calibration["margin"]
    grouped = {}
    for p, q, t in history:
        grouped.setdefault(p, []).append((q, t))
    eligible = [
        (p, mean(v[0] for v in values), mean(v[1] for v in values))
        for p, values in grouped.items()
        if mean(v[0] for v in values) - margin >= 0.8
    ]
    if not eligible:
        return {
            "state": "abstain",
            "reason": "no measured condition satisfies quality margin",
            "margin": margin,
        }
    p, q, t = min(eligible, key=lambda x: x[2])
    return {
        "state": "research_only",
        "point": p,
        "quality_mean": q,
        "time_mean": t,
        "margin": margin,
        "policy": policy,
        "production_recommendation": "abstain: independent process validation absent",
    }
