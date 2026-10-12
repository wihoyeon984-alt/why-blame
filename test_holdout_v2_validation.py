import unittest

from benchmark.holdout_v2.annotation import (
    Annotation,
    ClaimAnnotation,
)
from benchmark.holdout_v2.case import (
    GroundTruthClaim,
    HoldoutCase,
)
from benchmark.holdout_v2.validation import (
    ValidationError,
    validate_annotation_against_case,
)


def make_case():
    return HoldoutCase(
        schema_version=2,
        case_id="example_001",
        repository_url=(
            "https://github.com/"
            "example/project.git"
        ),
        repository_commit="abc123",
        frozen=True,
        claims={
            "claim_001": GroundTruthClaim(
                claim_id="claim_001",
                label="SUPPORTED",
            ),
            "claim_002": GroundTruthClaim(
                claim_id="claim_002",
                label="UNSUPPORTED",
            ),
        },
    )


def make_annotation():
    return Annotation(
        schema_version=2,
        case_id="example_001",
        completed=True,
        failure_stage="",
        failure_type="",
        confidence_level="VERY_HIGH",
        confidence_source="final_output",
        claims={
            "claim_001": ClaimAnnotation(
                status="PRESENTED",
                raw_evidence="Exact output",
            ),
            "claim_002": ClaimAnnotation(
                status="WITHHELD",
                raw_evidence="Not presented",
            ),
        },
    )


class TestHoldoutV2Validation(unittest.TestCase):

    def test_accepts_complete_matching_annotation(self):
        validate_annotation_against_case(
            make_case(),
            make_annotation(),
        )

    def test_rejects_case_id_mismatch(self):
        annotation = make_annotation()

        annotation = Annotation(
            schema_version=annotation.schema_version,
            case_id="different_001",
            completed=annotation.completed,
            failure_stage=annotation.failure_stage,
            failure_type=annotation.failure_type,
            confidence_level=(
                annotation.confidence_level
            ),
            confidence_source=(
                annotation.confidence_source
            ),
            claims=annotation.claims,
        )

        with self.assertRaisesRegex(
            ValidationError,
            "case_id mismatch",
        ):
            validate_annotation_against_case(
                make_case(),
                annotation,
            )

    def test_rejects_missing_claim_annotation(self):
        annotation = make_annotation()

        annotation = Annotation(
            schema_version=annotation.schema_version,
            case_id=annotation.case_id,
            completed=annotation.completed,
            failure_stage=annotation.failure_stage,
            failure_type=annotation.failure_type,
            confidence_level=(
                annotation.confidence_level
            ),
            confidence_source=(
                annotation.confidence_source
            ),
            claims={
                "claim_001": (
                    annotation.claims["claim_001"]
                ),
            },
        )

        with self.assertRaisesRegex(
            ValidationError,
            "missing claim annotations",
        ):
            validate_annotation_against_case(
                make_case(),
                annotation,
            )

    def test_rejects_unknown_claim_annotation(self):
        annotation = make_annotation()

        claims = dict(annotation.claims)
        claims["claim_999"] = ClaimAnnotation(
            status="PRESENTED",
            raw_evidence="Unknown claim",
        )

        annotation = Annotation(
            schema_version=annotation.schema_version,
            case_id=annotation.case_id,
            completed=annotation.completed,
            failure_stage=annotation.failure_stage,
            failure_type=annotation.failure_type,
            confidence_level=(
                annotation.confidence_level
            ),
            confidence_source=(
                annotation.confidence_source
            ),
            claims=claims,
        )

        with self.assertRaisesRegex(
            ValidationError,
            "unknown claim annotations",
        ):
            validate_annotation_against_case(
                make_case(),
                annotation,
            )


if __name__ == "__main__":
    unittest.main()
