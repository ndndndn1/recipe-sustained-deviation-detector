import unittest

from microvia.calibration import calibrate, plan_measured
from microvia.evaluation_v3 import CONTEXT, calibration_for, trial
from microvia.policies import recommend


class V3Tests(unittest.TestCase):
    def test_insufficient_pairs_abstain(self):
        self.assertEqual(
            calibrate({"context": CONTEXT, "measurements": []})["state"], "abstain"
        )

    def test_calibration_scope(self):
        c = calibration_for("bias")
        self.assertGreater(c["margin"], 0.1)
        self.assertEqual(
            recommend([((0, 0), 0.95, 1)], "calibrated-margin", c, {})["state"],
            "abstain",
        )

    def test_budget_counts_repeats(self):
        r = trial(4, "smooth", "uniform", "raw", True)
        self.assertEqual(r["budget"], 20)
        self.assertEqual(sum(t["reason"] == "repeat" for t in r["trace"]), 6)
        self.assertEqual(len({tuple(t["condition"]) for t in r["trace"]}), 14)

    def test_infeasible_not_dropped(self):
        r = trial(4, "infeasible", "uniform", "fixed-margin")
        self.assertTrue(r["no_feasible"])
        self.assertEqual(r["loss"], 1)

    def test_unscoped_calibrated_input_abstains(self):
        rows = [
            {
                "measurement_id": str(i),
                "context": CONTEXT,
                "condition": [i / 2, 0],
                "observed": 0.9,
                "duration": 10,
                "replicate_group": str(i),
                "calibration_source": "synthetic",
                "measured_at": f"2026-01-02T00:0{i}:00+00:00",
                "bath_age": 0,
                "temperature": 20,
                "agitation": 1,
            }
            for i in range(3)
        ]
        r = plan_measured(
            {"context": CONTEXT, "measurements": rows},
            None,
            "uniform",
            "calibrated-margin",
        )
        self.assertEqual(r["state"], "abstain")


class V3IntegrationTests(unittest.TestCase):
    def load(self):
        import json
        from pathlib import Path

        root = Path(__file__).resolve().parents[1] / "microvia/examples"
        return (
            json.loads((root / "calibration.json").read_text()),
            json.loads((root / "observations.json").read_text()),
        )

    def test_cli_calibration_plan_and_report(self):
        import json
        import subprocess
        import sys
        import tempfile
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            cal = Path(tmp) / "cal.json"
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "microvia",
                    "calibrate",
                    "--input",
                    str(root / "microvia/examples/calibration.json"),
                    "--output",
                    str(cal),
                ],
                cwd=root,
                check=True,
            )
            args = [
                sys.executable,
                "-m",
                "microvia",
                "plan-experiments",
                "--input",
                str(root / "microvia/examples/observations.json"),
                "--strategy",
                "uniform",
                "--recommendation-policy",
                "calibrated-margin",
                "--calibration",
                str(cal),
            ]
            r = json.loads(subprocess.check_output(args, cwd=root))
            self.assertEqual(r["state"], "research_only")
            self.assertIn("abstain", r["production_recommendation"])
            args[3] = "report"
            report = subprocess.check_output(args, cwd=root, text=True)
            self.assertIn("research_recommendation", report)

    def test_scope_failures_and_duplicate_reference(self):
        import copy

        d, o = self.load()
        c = calibrate(d)
        for variant in ("overlap", "drift", "controls", "context"):
            v = copy.deepcopy(o)
            if variant == "overlap":
                v["measurements"][0]["measurement_id"] = "cal-0"
            if variant == "drift":
                v["drift_detected"] = True
            if variant == "controls":
                v["measurements"][0]["temperature"] = 100
            if variant == "context":
                v["context"]["bath_id"] = "other"
                for r in v["measurements"]:
                    r["context"]["bath_id"] = "other"
            self.assertEqual(
                plan_measured(v, c, "uniform", "calibrated-margin")["state"], "abstain"
            )
        d["measurements"][1]["measurement_id"] = d["measurements"][0]["measurement_id"]
        with self.assertRaises(ValueError):
            calibrate(d)


class FailureAccountingTests(unittest.TestCase):
    def test_error_kept_in_denominator(self):
        from unittest.mock import patch

        from microvia.evaluation_v3 import safe_trial

        with patch(
            "microvia.evaluation_v3.trial", side_effect=RuntimeError("private detail")
        ):
            row = safe_trial(1, "smooth", "uniform", "raw")
        self.assertEqual(row["loss"], 1)
        self.assertTrue(row["violation"])
        self.assertEqual(row["error"], "RuntimeError")
