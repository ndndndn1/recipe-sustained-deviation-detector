"""Recipe-aware sustained-deviation detector; calibrated units are caller supplied."""
import json
import math
import sys
from dataclasses import dataclass, field


@dataclass
class Detector:
    centers: dict[str, float]
    threshold: float = 2.0
    persistence: int = 3
    streaks: dict[str, int] = field(default_factory=dict)
    last_time: dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        if self.threshold <= 0 or not math.isfinite(self.threshold) or self.persistence < 1:
            raise ValueError("Positive finite threshold and persistence required")
        if not self.centers or any(not math.isfinite(v) for v in self.centers.values()):
            raise ValueError("Finite recipe centers required")

    def observe(self, recipe: str, t: int, value: float) -> dict:
        if recipe not in self.centers or isinstance(value, bool) or not math.isfinite(value):
            raise ValueError("Unknown recipe or invalid measurement")
        if not isinstance(t, int) or isinstance(t, bool) or t < 0:
            raise ValueError("Non-negative integer sample index required")
        previous_time = self.last_time.get(recipe)
        if previous_time is not None and t <= previous_time:
            raise ValueError("Duplicate/out-of-order measurement")
        previous = self.streaks.get(recipe, 0)
        if previous_time is not None and t != previous_time + 1:
            previous = 0  # Missing observations cannot imply continuous deviation.
        residual = value - self.centers[recipe]
        above = abs(residual) > self.threshold
        streak = min(previous + 1, self.persistence) if above else 0
        self.streaks[recipe] = streak
        self.last_time[recipe] = t
        return {"recipe": recipe, "sample": t, "residual": residual, "above": above,
                "streak": streak, "alarm": streak == self.persistence}


def main():
    detector = Detector({"A": 0.0, "B": 40.0})
    for line in sys.stdin:
        row = json.loads(line)
        print(json.dumps(detector.observe(row["recipe"], row["t"], row["value"])))


if __name__ == "__main__":
    main()
