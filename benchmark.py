import json

from baseline.workload import result, samples
from solution import Detector


def evaluate(seed, persistence=3):
    detector = Detector({"A": 0.0, "B": 40.0}, persistence=persistence)
    false_alarms, first_detection = 0, {}
    for row in samples(seed):
        observation = detector.observe(row["recipe"], row["t"], row["value"])
        if observation["alarm"]:
            if not row["shifted"]:
                false_alarms += 1
            else:
                first_detection.setdefault(row["recipe"], row["t"] - 200 + 1)
    return {"false_alarms": false_alarms, "detection_delay_samples": first_detection}


def measure():
    report = result()
    for trial in report["trials"]:
        measured = evaluate(trial["seed"])
        trial["candidate"] = measured["false_alarms"]
        trial["detection_delay_samples"] = measured["detection_delay_samples"]
    return report


if __name__ == "__main__":
    print(json.dumps(measure()))
