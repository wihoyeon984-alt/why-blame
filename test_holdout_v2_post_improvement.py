import unittest
from pathlib import Path

from benchmark.holdout_v2.score_post_improvement import (
    PostImprovementError,
    evaluate_post_improvement,
    render_comparison,
)


class TestHoldoutV2PostImprovement(unittest.TestCase):

    def setUp(self):
        self.holdout_dir = (
            Path(__file__).parent
            / "benchmark"
            / "holdout_v2"
        )
        self.post_dir = (
            self.holdout_dir
            / "post_improvement"
        )

    def test_evaluates_preserved_post_improvement_artifacts(self):
        result = evaluate_post_improvement(
            holdout_dir=self.holdout_dir,
            post_dir=self.post_dir,
        )

        baseline = result["baseline"]
        post = result["post_improvement"]
        delta = result["delta"]

        self.assertEqual(
            baseline["supported_total"],
            20,
        )
        self.assertEqual(
            baseline["supported_presented"],
            17,
        )
        self.assertEqual(
            baseline["unsafe_presented"],
            0,
        )
        self.assertAlmostEqual(
            baseline["claim_precision"],
            1.0,
        )
        self.assertAlmostEqual(
            baseline["supported_recall"],
            0.85,
        )
        self.assertAlmostEqual(
            baseline["unsafe_presentation_rate"],
            0.0,
        )

        self.assertEqual(
            post["supported_total"],
            20,
        )
        self.assertEqual(
            post["supported_presented"],
            20,
        )
        self.assertEqual(
            post["unsafe_presented"],
            0,
        )
        self.assertAlmostEqual(
            post["claim_precision"],
            1.0,
        )
        self.assertAlmostEqual(
            post["supported_recall"],
            1.0,
        )
        self.assertAlmostEqual(
            post["unsafe_presentation_rate"],
            0.0,
        )

        self.assertEqual(
            delta["supported_presented"],
            3,
        )
        self.assertEqual(
            delta["unsafe_presented"],
            0,
        )
        self.assertAlmostEqual(
            delta["supported_recall"],
            0.15,
        )

    def test_reports_exactly_three_safe_improvements(self):
        result = evaluate_post_improvement(
            holdout_dir=self.holdout_dir,
            post_dir=self.post_dir,
        )

        improvements = result["improvements"]

        self.assertEqual(
            [
                (
                    item["case_id"],
                    item["claim_id"],
                    item["baseline_status"],
                    item["post_improvement_status"],
                )
                for item in improvements
            ],
            [
                (
                    "requests_003",
                    "claim_001",
                    "WITHHELD",
                    "PRESENTED",
                ),
                (
                    "rich_001",
                    "claim_002",
                    "WITHHELD",
                    "PRESENTED",
                ),
                (
                    "rich_002",
                    "claim_001",
                    "WITHHELD",
                    "PRESENTED",
                ),
            ],
        )

        for item in improvements:
            self.assertEqual(
                item["label"],
                "SUPPORTED",
            )

    def test_renders_comparison_report(self):
        result = evaluate_post_improvement(
            holdout_dir=self.holdout_dir,
            post_dir=self.post_dir,
        )

        rendered = render_comparison(result)

        self.assertIn(
            "Holdout v2 post-improvement comparison",
            rendered,
        )
        self.assertIn(
            "Supported presented:       17 / 20",
            rendered,
        )
        self.assertIn(
            "Supported presented:       20 / 20",
            rendered,
        )
        self.assertIn(
            "Supported recall:          0.850",
            rendered,
        )
        self.assertIn(
            "Supported recall:          1.000",
            rendered,
        )
        self.assertIn(
            "Supported recall:          +0.150",
            rendered,
        )
        self.assertIn(
            "Unsafe presented:          +0",
            rendered,
        )

    def test_missing_post_directory_is_rejected(self):
        missing = (
            self.holdout_dir
            / "missing_post_improvement"
        )

        with self.assertRaises(
            PostImprovementError
        ):
            evaluate_post_improvement(
                holdout_dir=self.holdout_dir,
                post_dir=missing,
            )


if __name__ == "__main__":
    unittest.main()
