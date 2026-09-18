"""Fixed synthetic benchmark; optimizer sees queried observations only."""

import math
import random
from statistics import median

GRID = [(i / 10, j / 10) for i in range(11) for j in range(11)]


def scenario(seed):
    rng = random.Random(seed + 4000)
    center = (rng.uniform(0.25, 0.75), rng.uniform(0.25, 0.75))

    def observe(point):
        x, y = point
        quality = max(0, 1 - 1.3 * (x - center[0]) ** 2 - 1.7 * (y - center[1]) ** 2)
        duration = 120 - 45 * x + 15 * y
        return quality, duration

    return observe


def choose(history, remaining):
    # Inverse-distance surrogate with explicit exploration bonus. No oracle access.
    def score(point):
        distances = [(math.dist(point, p), q, t) for p, q, t in history]
        nearest = min(d[0] for d in distances)
        weights = [(1 / (d * d + 0.01), q, t) for d, q, t in distances]
        total = sum(w for w, _, _ in weights)
        quality = sum(w * q for w, q, _ in weights) / total
        duration = sum(w * t for w, _, t in weights) / total
        return duration + 250 * max(0, 0.8 - quality) - 30 * nearest

    return min(remaining, key=score)


def run():
    results = []
    for seed in range(10):
        oracle = scenario(seed)
        initial = random.Random(seed).sample(GRID, 8)
        optimum = min(oracle(p)[1] for p in GRID if oracle(p)[0] >= 0.8)
        for method in ("uniform", "random", "adaptive"):
            history = [(p, *oracle(p)) for p in initial]
            remaining = [p for p in GRID if p not in initial]
            rng = random.Random(seed + 100)
            for _ in range(12):
                if method == "adaptive":
                    point = choose(history, remaining)
                elif method == "uniform":
                    point = max(
                        remaining,
                        key=lambda p: min(math.dist(p, h[0]) for h in history),
                    )
                else:
                    point = rng.choice(remaining)
                remaining.remove(point)
                history.append((point, *oracle(point)))
            feasible = [t for _, q, t in history if q >= 0.8]
            regret = min(feasible) - optimum if feasible else 120.0
            results.append(
                {
                    "seed": seed,
                    "method": method,
                    "observations": len(history),
                    "regret_minutes": regret,
                    "feasible_found": bool(feasible),
                }
            )
    medians = {
        m: median(r["regret_minutes"] for r in results if r["method"] == m)
        for m in ("uniform", "random", "adaptive")
    }
    baseline = min(medians["uniform"], medians["random"])
    passed = baseline > 0 and medians["adaptive"] <= 0.9 * baseline
    return {
        "evidence": "synthetic_unvalidated_response_surface",
        "runs": results,
        "median_regret_minutes": medians,
        "target_met": passed,
        "synthetic_v1_winner_not_deployment_default": "adaptive"
        if passed
        else min(("uniform", "random"), key=medians.get),
        "physical_process_validation": "not_run",
        "limitation": "deterministic smooth scenarios; no measurement noise or true plating kinetics",
    }
