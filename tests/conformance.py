import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from solution import Detector

checked = 0
for s in range(4):
    for above in [False, True]:
        detector = Detector({"A": 0}, streaks={"A": s})
        observed = detector.observe("A", 0, 3 if above else 0)
        expected = min(s + 1, 3) if above else 0
        assert observed["streak"] == expected and observed["alarm"] == (expected == 3)
        checked += 1
print(json.dumps({"conforms": True, "transitions_checked": checked}))
