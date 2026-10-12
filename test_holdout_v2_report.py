import io
import unittest
from contextlib import redirect_stdout

from benchmark.holdout_v2.report import (
    format_rate,
    print_confidence_metrics,
)


class TestHoldoutV2Report(unittest.TestCase):

    def test_format_rate_handles_values_and_none(self):
        self.assertEqual(
            format_rate(1.0),
            "1.000",
        )
        self.assertEqual(
            format_rate(0.5),
            "0.500",
        )
        self.assertEqual(
            format_rate(None),
            "N/A",
        )

    def test_report_renders_metrics_in_confidence_order(self):
        metrics = {
            "MEDIUM": {
                "case_count": 1,
                "supported_total": 2,
                "supported_presented": 1,
                "total_presentations": 1,
                "unsafe_presented": 0,
                "claim_precision": 1.0,
                "supported_recall": 0.5,
                "unsafe_presentation_rate": 0.0,
            },
            "VERY_HIGH": {
                "case_count": 2,
                "supported_total": 4,
                "supported_presented": 4,
                "total_presentations": 4,
                "unsafe_presented": 0,
                "claim_precision": 1.0,
                "supported_recall": 1.0,
                "unsafe_presentation_rate": 0.0,
            },
            "HIGH": {
                "case_count": 1,
                "supported_total": 1,
                "supported_presented": 1,
                "total_presentations": 1,
                "unsafe_presented": 0,
                "claim_precision": 1.0,
                "supported_recall": 1.0,
                "unsafe_presentation_rate": 0.0,
            },
        }

        output = io.StringIO()

        with redirect_stdout(output):
            print_confidence_metrics(metrics)

        rendered = output.getvalue()

        self.assertIn(
            "Confidence-stratified metrics",
            rendered,
        )
        self.assertIn(
            "Claim precision:           1.000",
            rendered,
        )
        self.assertIn(
            "Supported recall:          0.500",
            rendered,
        )
        self.assertIn(
            "Unsafe presentation rate:  0.000",
            rendered,
        )

        self.assertLess(
            rendered.index("VERY_HIGH"),
            rendered.index("HIGH"),
        )
        self.assertLess(
            rendered.index("HIGH"),
            rendered.index("MEDIUM"),
        )

    def test_report_uses_na_for_zero_denominators(self):
        metrics = {
            "LOW": {
                "case_count": 1,
                "supported_total": 0,
                "supported_presented": 0,
                "total_presentations": 0,
                "unsafe_presented": 0,
                "claim_precision": None,
                "supported_recall": None,
                "unsafe_presentation_rate": None,
            },
        }

        output = io.StringIO()

        with redirect_stdout(output):
            print_confidence_metrics(metrics)

        rendered = output.getvalue()

        self.assertIn(
            "LOW",
            rendered,
        )
        self.assertIn(
            "Claim precision:           N/A",
            rendered,
        )
        self.assertIn(
            "Supported recall:          N/A",
            rendered,
        )
        self.assertIn(
            "Unsafe presentation rate:  N/A",
            rendered,
        )

    def test_empty_metrics_are_reported_explicitly(self):
        output = io.StringIO()

        with redirect_stdout(output):
            print_confidence_metrics({})

        self.assertIn(
            "No confidence data.",
            output.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
