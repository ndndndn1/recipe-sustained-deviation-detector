import itertools
import unittest
from pathlib import Path

from microvia.benchmark import run
from microvia.core import (
    analyze,
    copper_balance,
    gate,
    mask_metrics,
    plan,
    read_csv,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]


class MicroviaTests(unittest.TestCase):
    def rows(self):
        return read_csv(ROOT / "microvia/example.csv")["accepted"]

    def test_faraday_independent_charge_balance(self):
        # 1 A/dm2 for 60 min on 1 dm2 deposits ~1.1855 g Cu at eta=1.
        r = copper_balance(1, 60, 1, 100, 80)
        self.assertAlmostEqual(r["planar_equivalent_thickness_um"], 13.230, delta=0.014)
        self.assertAlmostEqual(r["cylindrical_void_volume_um3"], 628318.5307, places=3)
        self.assertAlmostEqual(
            copper_balance(2, 60, 0.5, 100, 80)["planar_equivalent_thickness_um"],
            r["planar_equivalent_thickness_um"],
        )

    def test_bad_measurements(self):
        for field, value in [
            ("diameter_um", "nan"),
            ("time_min", 0),
            ("efficiency", 1.1),
            ("fill_ratio", -1),
            ("source", ""),
            ("timestamp", "2026-01-01"),
        ]:
            row = dict(self.rows()[0])
            row[field] = value
            self.assertEqual(len(validate([row])["quarantined"]), 1)

    def test_duplicate_and_reordered(self):
        rows = self.rows()
        self.assertEqual(len(validate([rows[0], rows[0]])["quarantined"]), 1)
        self.assertEqual(len(validate(rows[::-1])["quarantined"]), 2)

    def test_mask_exact_area(self):
        r = mask_metrics([[1, 1, 0], [1, 2, 0]], 2)
        self.assertEqual(r["area_fill_ratio"], 0.75)
        self.assertEqual(r["copper_area_um2"], 12)
        self.assertEqual(r["unfilled_area_um2"], 4)
        for mask in [[], [[0]], [[1], [1, 2]], [[3]]]:
            with self.assertRaises(ValueError):
                mask_metrics(mask, 1)

    def test_bounded_plan_and_unknown(self):
        v = validate(self.rows())
        p = plan(v, "SYNTHETIC", "cylindrical")
        self.assertEqual(p["current_a_dm2"], [1, 1.5, 2])
        self.assertEqual(plan(v, "UNKNOWN", "cylindrical")["state"], "abstain")
        v["quarantined"] = [{"reason": "bad input"}]
        self.assertEqual(plan(v, "SYNTHETIC", "cylindrical")["state"], "abstain")

    def test_geometry_and_lot_separation(self):
        rows = self.rows()
        rows[2]["depth_um"] = 100
        self.assertEqual(
            plan(validate(rows), "SYNTHETIC", "cylindrical")["state"], "abstain"
        )
        rows[2]["lot"] = "OTHER"
        self.assertEqual(len(analyze(validate(rows))["strata"]), 2)

    def test_lean_boolean_contract_exhaustive(self):
        for bits in itertools.product([False, True], repeat=4):
            self.assertEqual(gate(*bits), bits == (True, True, True, True))

    def test_fixed_budget_reproducibility(self):
        first = run()
        self.assertEqual(first, run())
        self.assertEqual(len(first["runs"]), 30)
        self.assertTrue(all(r["observations"] == 20 for r in first["runs"]))
        self.assertEqual(first["physical_process_validation"], "not_run")


if __name__ == "__main__":
    unittest.main()
