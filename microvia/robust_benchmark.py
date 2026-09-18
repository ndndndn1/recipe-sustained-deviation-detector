"""Held-out stress evaluation. Oracle is available only to the evaluator."""

import hashlib
import json
import math
import random
from statistics import mean

from .benchmark import GRID, choose

FAMILIES = ("smooth", "interaction", "narrow", "drift")
METHODS = ("uniform", "random", "adaptive", "conservative")


def truth(seed, family, point, step):
    rng = random.Random(seed + 87001)
    cx, cy = rng.uniform(0.15, 0.85), rng.uniform(0.15, 0.85)
    x, y = point
    if family == "drift":
        cx += 0.22 * step / 20
    scale = 3.5 if family == "narrow" else 1.4
    quality = 1 - scale * ((x - cx) ** 2 + (y - cy) ** 2)
    if family == "interaction":
        quality -= 0.22 * math.sin(9 * x) * math.sin(7 * y)
    duration = 110 + rng.uniform(-35, 35) * x + rng.uniform(-35, 35) * y + 20 * x * y
    return max(0, min(1, quality)), duration


def observe(seed, family, point, step):
    quality, duration = truth(seed, family, point, step)
    # Common random numbers per point/time across methods; independent of order of evaluation.
    rng = random.Random(f"{seed}:{family}:{point}:{step}")
    return quality + rng.gauss(0, 0.04), duration + rng.gauss(0, 2)


def conservative(history, remaining):
    def score(point):
        neighbors = sorted((math.dist(point, p), q, t) for p, q, t in history)[:4]
        q = mean(v[1] for v in neighbors)
        t = mean(v[2] for v in neighbors)
        distance = neighbors[0][0]
        return t + 300 * max(0, 0.8 - (q - 0.08 - distance * 0.2)) - 15 * distance

    return min(remaining, key=score)


def trial(seed, family, method, final_margin=None):
    initial = random.Random(seed).sample(GRID, 8)
    history = [(p, *observe(seed, family, p, i)) for i, p in enumerate(initial)]
    remaining = [p for p in GRID if p not in initial]
    rng = random.Random(seed + 22)
    for step in range(8, 20):
        if method == "adaptive":
            point = choose(history, remaining)
        elif method == "conservative":
            point = conservative(history, remaining)
        elif method == "random":
            point = rng.choice(remaining)
        else:
            point = max(
                remaining, key=lambda p: min(math.dist(p, h[0]) for h in history)
            )
        remaining.remove(point)
        history.append((point, *observe(seed, family, point, step)))
    # Recommendation uses observations, never true quality or the oracle optimum.
    margin = (
        (0.08 if method == "conservative" else 0)
        if final_margin is None
        else final_margin
    )
    eligible = [h for h in history if h[1] >= 0.8 + margin]
    chosen = min(eligible, key=lambda h: h[2])[0] if eligible else None
    feasible = [
        truth(seed, family, p, 20)[1]
        for p in GRID
        if truth(seed, family, p, 20)[0] >= 0.8
    ]
    optimum = min(feasible) if feasible else None
    violation = False
    loss = 1.0
    if chosen is not None:
        q, t = truth(seed, family, chosen, 20)
        violation = q < 0.8
        if not violation and optimum is not None:
            loss = max(0, (t - optimum) / 120)
    return {
        "seed": seed,
        "family": family,
        "method": method,
        "budget": 20,
        "loss": loss,
        "violation": violation,
        "abstained": chosen is None,
        "no_feasible_truth": optimum is None,
    }


def interval(differences):
    rng = random.Random(719)
    values = sorted(
        mean(rng.choices(differences, k=len(differences))) for _ in range(2000)
    )
    return [values[49], values[1949]]


def run():
    development = [trial(s, f, m) for s in range(20) for f in FAMILIES for m in METHODS]
    candidate = min(
        ("adaptive", "conservative"),
        key=lambda m: mean(r["loss"] for r in development if r["method"] == m),
    )
    baseline = min(
        ("uniform", "random"),
        key=lambda m: mean(r["loss"] for r in development if r["method"] == m),
    )
    test = [trial(s, f, m) for s in range(100, 150) for f in FAMILIES for m in METHODS]
    summary = {
        m: {
            "loss": mean(r["loss"] for r in test if r["method"] == m),
            "violation_rate": mean(r["violation"] for r in test if r["method"] == m),
            "abstention_rate": mean(r["abstained"] for r in test if r["method"] == m),
        }
        for m in METHODS
    }
    # Resample seeds as clusters, keeping the four families together.
    differences = [
        mean(r["loss"] for r in test if r["seed"] == s and r["method"] == baseline)
        - mean(r["loss"] for r in test if r["seed"] == s and r["method"] == candidate)
        for s in range(100, 150)
    ]
    ci = interval(differences)
    passed = (
        ci[0] > 0
        and summary[candidate]["loss"] <= 0.9 * summary[baseline]["loss"]
        and summary[candidate]["violation_rate"] <= summary[baseline]["violation_rate"]
    )
    return {
        "protocol": "robust-v2",
        "candidate_selected_on_development": candidate,
        "baseline_selected_on_development": baseline,
        "summary": summary,
        "paired_seed_cluster_gain_ci95": ci,
        "promotion_passed": passed,
        "deployment_decision": "research_only_no_factory_validation",
        "per_family": {
            f: {
                m: mean(
                    r["loss"] for r in test if r["family"] == f and r["method"] == m
                )
                for m in METHODS
            }
            for f in FAMILIES
        },
        "runs": test,
        "development_runs": development,
        "source_sha256": hashlib.sha256(
            __import__("pathlib").Path(__file__).read_bytes()
        ).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
