import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from benchmark import evaluate

# Inject incorrect persistence configuration into the real implementation.
detected = evaluate(11, persistence=1)["false_alarms"] > 0
print(json.dumps({"defect_detected": detected}))
sys.exit(1 if detected else 0)
