import unittest
from types import SimpleNamespace

from benchmark.holdout_v2.validator import (
    CrossReferenceError,
    validate_candidate_reference,
    validate_candidate_set,
)


def make_candidate(
    candidate_id="urllib3_001",
    repository_url="https://github.com/urllib3/urllib3.git",
    repository_commit="a" * 40,
):
    return SimpleNamespace(
        schema_version=2,
        candidate_id=candidate_id,
        repository=SimpleNamespace(
            url=repository_url,
            commit=repository_commit,
        ),
    )


def make_case(
    case_id="urllib3_001",
    repository_url="https://github.com/urllib3/urllib3.git",
    repository_commit="a" * 40,
    claims=None,
):
    return SimpleNamespace(
        schema_version=2,
        case_id=case_id,
        repository_url=repository_url,
        repository_commit=repository_commit,
        claims=claims or {
            "claim_001": SimpleNamespace(
                claim_id="claim_001",
                label="SUPPORTED",
            ),
        },
    )


def make_annotation(
    case_id="urllib3_001",
    claim_ids=None,
):
    claim_ids = claim_ids or [
        "claim_001",
    ]

    return SimpleNamespace(
        schema_version=2,
        case_id=case_id,
        claims={
            claim_id: SimpleNamespace(
                status="PRESENTED",
                raw_evidence="evidence",
            )
            for claim_id in claim_ids
        },
    )


class TestHoldoutV2Validator(unittest.TestCase):

    def test_valid_candidate_reference(self):
        validate_candidate_reference(
            make_candidate(),
            make_case(),
        )

    def test_candidate_case_id_mismatch(self):
        with self.assertRaises(
            CrossReferenceError
        ):
            validate_candidate_reference(
                make_candidate(),
                make_case(
                    case_id="urllib3_999",
                ),
            )

    def test_repository_url_mismatch(self):
        with self.assertRaises(
            CrossReferenceError
        ):
            validate_candidate_reference(
                make_candidate(),
                make_case(
                    repository_url=(
                        "https://github.com/"
                        "django/django.git"
                    ),
                ),
            )

    def test_repository_commit_mismatch(self):
        with self.assertRaises(
            CrossReferenceError
        ):
            validate_candidate_reference(
                make_candidate(),
                make_case(
                    repository_commit="b" * 40,
                ),
            )

    def test_duplicate_candidate_id(self):
        candidates = [
            make_candidate(),
            make_candidate(),
        ]

        with self.assertRaises(
            CrossReferenceError
        ):
            validate_candidate_set(
                candidates,
            )

    def test_valid_annotation_reference(self):
        validate_candidate_reference(
            make_candidate(),
            make_case(),
            make_annotation(),
        )

    def test_unknown_annotation_claim(self):
        with self.assertRaises(
            CrossReferenceError
        ):
            validate_candidate_reference(
                make_candidate(),
                make_case(),
                make_annotation(
                    claim_ids=[
                        "claim_999",
                    ],
                ),
            )


if __name__ == "__main__":
    unittest.main()
