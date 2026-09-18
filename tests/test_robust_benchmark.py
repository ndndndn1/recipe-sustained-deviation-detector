import unittest
from unittest.mock import patch

from microvia.robust_benchmark import conservative, interval, trial


class RobustTests(unittest.TestCase):
    def test_abstention_is_not_success(self):
        with patch("microvia.robust_benchmark.observe", return_value=(0.1, 1)):
            r = trial(100, "smooth", "uniform")
        self.assertTrue(r["abstained"])
        self.assertEqual(r["loss"], 1)
        self.assertEqual(r["budget"], 20)

    def test_noisy_false_feasibility_penalized(self):
        with (
            patch("microvia.robust_benchmark.observe", return_value=(1, 1)),
            patch("microvia.robust_benchmark.truth", return_value=(0.1, 1)),
        ):
            r = trial(100, "smooth", "uniform")
        self.assertTrue(r["violation"])
        self.assertTrue(r["no_feasible_truth"])
        self.assertEqual(r["loss"], 1)

    def test_selector_cannot_call_oracle(self):
        with patch(
            "microvia.robust_benchmark.truth", side_effect=AssertionError("oracle leak")
        ):
            p = conservative([((0, 0), 0.9, 100)], [(1, 1), (0.1, 0.1)])
        self.assertIn(p, [(1, 1), (0.1, 0.1)])

    def test_repeatable_and_zero_interval(self):
        self.assertEqual(
            trial(111, "drift", "conservative"), trial(111, "drift", "conservative")
        )
        self.assertEqual(interval([0] * 50), [0, 0])
