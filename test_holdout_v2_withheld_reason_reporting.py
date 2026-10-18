import io
import unittest
from contextlib import redirect_stdout

from benchmark.holdout_v2.annotation import (
    Annotation,
    ClaimAnnotation,
    VALID_WITHHELD_REASONS,
)
from benchmark.holdout_v2.metrics import (
    summarize_withheld_reasons,
)
from benchmark.holdout_v2.report import (
    print_withheld_reason_summary,
)


def make_annotation(claims):
    return Annotation(
        schema_version=2,
        case_id="example_001",
        completed=True,
        failure_stage="",
        failure_type="",
        confidence_level="VERY_HIGH",
        confidence_source="final_output",
        claims=claims,
    )


class TestWithheldReasonReporting(unittest.TestCase):
    def test_empty_annotations_have_zero_counts(self):
        summary = summarize_withheld_reasons({})

        self.assertEqual(summary["total"], 0)
        self.assertEqual(summary["specified"], 0)
        self.assertEqual(summary["unspecified"], 0)
        self.assertEqual(
            set(summary["by_reason"]),
            VALID_WITHHELD_REASONS,
        )
        self.assertTrue(
            all(
                count == 0
                for count in summary[
                    "by_reason"
                ].values()
            )
        )

    def test_reasonless_withheld_is_unspecified(self):
        annotation = make_annotation(
            {
                "claim_001": ClaimAnnotation(
                    status="WITHHELD",
                    raw_evidence="Not presented",
                ),
            }
        )

        summary = summarize_withheld_reasons(
            {"example_001": annotation}
        )

        self.assertEqual(summary["total"], 1)
        self.assertEqual(summary["specified"], 0)
        self.assertEqual(summary["unspecified"], 1)

    def test_specified_reason_is_counted(self):
        annotation = make_annotation(
            {
                "claim_001": ClaimAnnotation(
                    status="WITHHELD",
                    raw_evidence=(
                        "No supporting evidence "
                        "was observed."
                    ),
                    withheld_reason="NOT_OBSERVED",
                ),
            }
        )

        summary = summarize_withheld_reasons(
            {"example_001": annotation}
        )

        self.assertEqual(summary["total"], 1)
        self.assertEqual(summary["specified"], 1)
        self.assertEqual(summary["unspecified"], 0)
        self.assertEqual(
            summary["by_reason"]["NOT_OBSERVED"],
            1,
        )

    def test_non_withheld_claims_are_excluded(self):
        annotation = make_annotation(
            {
                "claim_001": ClaimAnnotation(
                    status="PRESENTED",
                    raw_evidence="Exact output",
                ),
                "claim_002": ClaimAnnotation(
                    status="ABSTAINED",
                    raw_evidence=(
                        "Explicit abstention"
                    ),
                ),
            }
        )

        summary = summarize_withheld_reasons(
            {"example_001": annotation}
        )

        self.assertEqual(summary["total"], 0)
        self.assertEqual(summary["specified"], 0)
        self.assertEqual(summary["unspecified"], 0)

    def test_summary_invariants_hold(self):
        annotation = make_annotation(
            {
                "claim_001": ClaimAnnotation(
                    status="WITHHELD",
                    raw_evidence="Not presented",
                ),
                "claim_002": ClaimAnnotation(
                    status="WITHHELD",
                    raw_evidence="Conflict observed",
                    withheld_reason=(
                        "CONFLICTING_EVIDENCE"
                    ),
                ),
                "claim_003": ClaimAnnotation(
                    status="WITHHELD",
                    raw_evidence="Not observed",
                    withheld_reason="NOT_OBSERVED",
                ),
            }
        )

        summary = summarize_withheld_reasons(
            {"example_001": annotation}
        )

        self.assertEqual(
            summary["total"],
            (
                summary["specified"]
                + summary["unspecified"]
            ),
        )
        self.assertEqual(
            summary["specified"],
            sum(summary["by_reason"].values()),
        )

    def test_report_renders_reason_coverage(self):
        summary = {
            "total": 3,
            "specified": 2,
            "unspecified": 1,
            "by_reason": {
                "CONFLICTING_EVIDENCE": 1,
                "INSUFFICIENT_EVIDENCE": 0,
                "NOT_OBSERVED": 1,
                "OUTSIDE_SUPPORTED_SCOPE": 0,
            },
        }

        output = io.StringIO()

        with redirect_stdout(output):
            print_withheld_reason_summary(
                summary
            )

        rendered = output.getvalue()

        self.assertIn(
            "WITHHELD reason coverage",
            rendered,
        )
        self.assertIn(
            "Total WITHHELD:        3",
            rendered,
        )
        self.assertIn(
            "Reason specified:      2",
            rendered,
        )
        self.assertIn(
            "Reason unspecified:    1",
            rendered,
        )
        self.assertIn(
            "NOT_OBSERVED: 1",
            rendered,
        )


if __name__ == "__main__":
    unittest.main()
