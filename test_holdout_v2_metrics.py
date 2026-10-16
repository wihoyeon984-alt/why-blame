import unittest

from benchmark.holdout_v2.annotation import (
    Annotation,
    ClaimAnnotation,
)
from benchmark.holdout_v2.case import (
    GroundTruthClaim,
    HoldoutCase,
)
from benchmark.holdout_v2.metrics import (
    compute_confidence_metrics,
)


def make_case(
    case_id,
    claims,
):
    return HoldoutCase(
        schema_version=2,
        case_id=case_id,
        repository_url=(
            "https://github.com/"
            "example/project.git"
        ),
        repository_commit="abc123",
        frozen=True,
        claims={
            claim_id: GroundTruthClaim(
                claim_id=claim_id,
                label=label,
            )
            for claim_id, label in claims.items()
        },
    )


def make_annotation(
    case_id,
    confidence,
    statuses,
):
    return Annotation(
        schema_version=2,
        case_id=case_id,
        completed=True,
        failure_stage="",
        failure_type="",
        confidence_level=confidence,
        confidence_source="final_output",
        claims={
            claim_id: ClaimAnnotation(
                status=status,
                raw_evidence="test evidence",
            )
            for claim_id, status in statuses.items()
        },
    )


class TestHoldoutV2Metrics(unittest.TestCase):

    def test_safe_presentations_are_grouped_by_confidence(self):
        case = make_case(
            "case_001",
            {
                "claim_001": "SUPPORTED",
                "claim_002": "UNSUPPORTED",
            },
        )

        annotation = make_annotation(
            "case_001",
            "VERY_HIGH",
            {
                "claim_001": "PRESENTED",
                "claim_002": "WITHHELD",
            },
        )

        metrics = compute_confidence_metrics(
            [case],
            {
                "case_001": annotation,
            },
        )

        group = metrics["VERY_HIGH"]

        self.assertEqual(
            group["case_count"],
            1,
        )
        self.assertEqual(
            group["supported_total"],
            1,
        )
        self.assertEqual(
            group["supported_presented"],
            1,
        )
        self.assertEqual(
            group["total_presentations"],
            1,
        )
        self.assertEqual(
            group["unsafe_presented"],
            0,
        )
        self.assertEqual(
            group["claim_precision"],
            1.0,
        )
        self.assertEqual(
            group["supported_recall"],
            1.0,
        )
        self.assertEqual(
            group["unsafe_presentation_rate"],
            0.0,
        )

    def test_unsafe_presentation_is_counted(self):
        case = make_case(
            "case_002",
            {
                "claim_001": "SUPPORTED",
                "claim_002": "UNSUPPORTED",
            },
        )

        annotation = make_annotation(
            "case_002",
            "MEDIUM",
            {
                "claim_001": "MISSED",
                "claim_002": "UNSAFE_PRESENTED",
            },
        )

        metrics = compute_confidence_metrics(
            [case],
            {
                "case_002": annotation,
            },
        )

        group = metrics["MEDIUM"]

        self.assertEqual(
            group["supported_presented"],
            0,
        )
        self.assertEqual(
            group["total_presentations"],
            1,
        )
        self.assertEqual(
            group["unsafe_presented"],
            1,
        )
        self.assertEqual(
            group["claim_precision"],
            0.0,
        )
        self.assertEqual(
            group["supported_recall"],
            0.0,
        )
        self.assertEqual(
            group["unsafe_presentation_rate"],
            1.0,
        )

    def test_zero_presentations_produce_na_rates(self):
        case = make_case(
            "case_003",
            {
                "claim_001": "SUPPORTED",
                "claim_002": "UNSUPPORTED",
            },
        )

        annotation = make_annotation(
            "case_003",
            "LOW",
            {
                "claim_001": "MISSED",
                "claim_002": "WITHHELD",
            },
        )

        metrics = compute_confidence_metrics(
            [case],
            {
                "case_003": annotation,
            },
        )

        group = metrics["LOW"]

        self.assertEqual(
            group["total_presentations"],
            0,
        )
        self.assertIsNone(
            group["claim_precision"]
        )
        self.assertEqual(
            group["supported_recall"],
            0.0,
        )
        self.assertIsNone(
            group[
                "unsafe_presentation_rate"
            ]
        )

    def test_multiple_cases_in_same_confidence_are_aggregated(self):
        cases = [
            make_case(
                "case_001",
                {
                    "claim_001": "SUPPORTED",
                },
            ),
            make_case(
                "case_002",
                {
                    "claim_001": "SUPPORTED",
                },
            ),
        ]

        annotations = {
            "case_001": make_annotation(
                "case_001",
                "HIGH",
                {
                    "claim_001": "PRESENTED",
                },
            ),
            "case_002": make_annotation(
                "case_002",
                "HIGH",
                {
                    "claim_001": "MISSED",
                },
            ),
        }

        metrics = compute_confidence_metrics(
            cases,
            annotations,
        )

        group = metrics["HIGH"]

        self.assertEqual(
            group["case_count"],
            2,
        )
        self.assertEqual(
            group["supported_total"],
            2,
        )
        self.assertEqual(
            group["supported_presented"],
            1,
        )
        self.assertEqual(
            group["supported_recall"],
            0.5,
        )

    def test_case_annotation_mismatch_is_rejected(self):
        case = make_case(
            "case_001",
            {
                "claim_001": "SUPPORTED",
            },
        )

        annotation = make_annotation(
            "different_001",
            "HIGH",
            {
                "claim_001": "PRESENTED",
            },
        )

        with self.assertRaises(ValueError):
            compute_confidence_metrics(
                [case],
                {
                    "case_001": annotation,
                },
            )


if __name__ == "__main__":
    unittest.main()
