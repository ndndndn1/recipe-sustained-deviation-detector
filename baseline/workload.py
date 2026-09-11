"""Synthetic recipe streams. Not semiconductor production measurements."""
import hashlib
import json
import random

SEEDS = [11, 29, 47]
CONDITIONS = "2 recipes x 300 observations; isolated spikes before t=200; sustained shift from t=200"


def samples(seed):
    rng = random.Random(seed)
    result = []
    for recipe, center in [("A", 0.0), ("B", 40.0)]:
        for t in range(300):
            shifted = t >= 200
            spike = t < 200 and t % 13 == seed % 13
            value = center + rng.uniform(-0.3, 0.3) + (2.8 if shifted else 3.0 if spike else 0.0)
            result.append({"recipe": recipe, "t": t, "value": value, "center": center, "shifted": shifted})
    return result


DATASET_HASH = hashlib.sha256(json.dumps([samples(s) for s in SEEDS], sort_keys=True).encode()).hexdigest()


def simple_threshold(data):
    return sum(not row["shifted"] and abs(row["value"] - row["center"]) > 2.0 for row in data)


def result():
    return {"metric": "false_alarms", "unit": "count", "conditions": CONDITIONS, "dataset_hash": DATASET_HASH,
            "trials": [{"seed": s, "baseline": simple_threshold(samples(s))} for s in SEEDS]}


if __name__ == "__main__":
    print(json.dumps(result()))
