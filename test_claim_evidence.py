import unittest

from claim_evidence import (
    BEHAVIOR,
    CAUSE,
    CONFLICTING,
    REVERT_CAUSE,
    REVERT_FACT,
    SUPPORTED,
    UNVERIFIED,
    evaluate_claim,
    make_claim,
    make_evidence,
)


class TestClaimEvidence(unittest.TestCase):

    def test_diff_supports_behavior_claim(self):
        claim = make_claim(
            "String input is encoded as UTF-8.",
            BEHAVIOR,
            [
                make_evidence(
                    "DIFF",
                    "src/requests/utils.py:137-138",
                )
            ],
        )

        result = evaluate_claim(claim)

        self.assertEqual(
            result["status"],
            SUPPORTED,
        )

    def test_unverified_cause_is_not_supported(self):
        claim = make_claim(
            "The change improves performance.",
            CAUSE,
            [],
        )

        result = evaluate_claim(claim)

        self.assertEqual(
            result["status"],
            UNVERIFIED,
        )

    def test_pr_can_support_cause_claim(self):
        claim = make_claim(
            "The change fixes incorrect byte-length handling.",
            CAUSE,
            [
                make_evidence(
                    "PR",
                    "#6589",
                )
            ],
        )

        result = evaluate_claim(claim)

        self.assertEqual(
            result["status"],
            SUPPORTED,
        )

    def test_revert_commit_supports_revert_fact(self):
        claim = make_claim(
            "The earlier change was explicitly reverted.",
            REVERT_FACT,
            [
                make_evidence(
                    "REVERT",
                    "bb7be1f6",
                )
            ],
        )

        result = evaluate_claim(claim)

        self.assertEqual(
            result["status"],
            SUPPORTED,
        )

    def test_revert_without_cause_evidence_stays_unverified(self):
        claim = make_claim(
            "The change was reverted because it introduced a bug.",
            REVERT_CAUSE,
            [
                make_evidence(
                    "REVERT",
                    "bb7be1f6",
                )
            ],
        )

        result = evaluate_claim(claim)

        self.assertEqual(
            result["status"],
            UNVERIFIED,
        )

    def test_conflicting_evidence_blocks_claim(self):
        claim = make_claim(
            "The change fixes payment validation.",
            CAUSE,
            [
                make_evidence(
                    "COMMIT",
                    "fix payment validation",
                ),
                make_evidence(
                    "PR",
                    "Improve image rendering",
                    supports=False,
                ),
            ],
        )

        result = evaluate_claim(claim)

        self.assertEqual(
            result["status"],
            CONFLICTING,
        )


if __name__ == "__main__":
    unittest.main()