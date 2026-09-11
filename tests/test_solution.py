import math
import unittest

from benchmark import evaluate
from baseline.workload import SEEDS
from solution import Detector


class DetectorTests(unittest.TestCase):
    def test_false_alarms_and_sustained_shift_latency(self):
        for seed in SEEDS:
            report = evaluate(seed)
            self.assertEqual(report["false_alarms"], 0)
            self.assertEqual(report["detection_delay_samples"], {"A": 3, "B": 3})

    def test_recipes_are_independent(self):
        d = Detector({"A": 0, "B": 40})
        self.assertFalse(d.observe("A", 0, 3)["alarm"])
        self.assertFalse(d.observe("B", 0, 43)["alarm"])
        self.assertFalse(d.observe("A", 1, 3)["alarm"])
        self.assertTrue(d.observe("A", 2, 3)["alarm"])
        self.assertFalse(d.observe("B", 1, 40)["alarm"])

    def test_gap_breaks_continuity(self):
        d = Detector({"A": 0})
        d.observe("A", 0, 3)
        d.observe("A", 1, 3)
        self.assertEqual(d.observe("A", 3, 3)["streak"], 1)

    def test_bad_values_and_reordered_samples_rejected(self):
        d = Detector({"A": 0})
        for v in [math.nan, math.inf, True]:
            with self.assertRaises(ValueError):
                d.observe("A", 0, v)
        d.observe("A", 0, 1)
        with self.assertRaises(ValueError):
            d.observe("A", 0, 1)
        with self.assertRaises(ValueError):
            d.observe("unknown", 1, 1)
