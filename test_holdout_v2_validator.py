import unittest

from benchmark.holdout_v2.validator import (
    validate_candidate_reference,
    validate_candidate_set,
)


class TestHoldoutV2Validator(unittest.TestCase):

    def test_valid_candidate_reference(self):
        cases = {
            "urllib3_001": {
                "repository": "urllib3",
            }
        }

        candidate = {
            "candidate_id": "cand_001",
            "case_id": "urllib3_001",
            "repository": "urllib3",
        }

        validate_candidate_reference(
            cases,
            candidate,
        )

    def test_missing_case_reference(self):
        cases = {}

        candidate = {
            "candidate_id": "cand_001",
            "case_id": "urllib3_001",
            "repository": "urllib3",
        }

        with self.assertRaises(ValueError):
            validate_candidate_reference(
                cases,
                candidate,
            )

    def test_repository_mismatch(self):
        cases = {
            "urllib3_001": {
                "repository": "urllib3",
            }
        }

        candidate = {
            "candidate_id": "cand_001",
            "case_id": "urllib3_001",
            "repository": "django",
        }

        with self.assertRaises(ValueError):
            validate_candidate_reference(
                cases,
                candidate,
            )

    def test_unknown_claim_reference(self):
        cases = {
            "urllib3_001": {
                "repository": "urllib3",
                "claims": [
                    "C001",
                    "C002",
                ],
            }
        }

        candidate = {
            "candidate_id": "cand_001",
            "case_id": "urllib3_001",
            "repository": "urllib3",
            "claim_id": "C999",
        }

        with self.assertRaises(ValueError):
            validate_candidate_reference(
                cases,
                candidate,
            )

    def test_duplicate_candidate_id(self):
        candidates = [
            {
                "candidate_id": "cand_001",
            },
            {
                "candidate_id": "cand_001",
            },
        ]

        with self.assertRaises(ValueError):
            validate_candidate_set(
                candidates,
            )


if __name__ == "__main__":
    unittest.main()
