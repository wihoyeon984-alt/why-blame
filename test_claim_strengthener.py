import unittest

from claim_evidence import (
    BEHAVIOR,
    make_claim,
)
from claim_strengthener import (
    KEEP_RAW,
    STRENGTHENABLE,
    collect_strengthenable_claims,
    evaluate_strengthening,
)


class TestClaimStrengthener(unittest.TestCase):

    def make_behavior(
        self,
        text,
        source_event="final123",
    ):
        claim = make_claim(
            text,
            BEHAVIOR,
            [],
        )

        claim["target_relevant"] = True
        claim["source_event"] = source_event

        return claim

    def test_matching_final_commit_can_strengthen_behavior(self):
        claim = self.make_behavior(
            (
                "Added code: "
                "elif verify is True and not "
                "has_poolmanager_ssl_context:"
            )
        )

        timeline = [
            {
                "hash": "final123",
                "message": (
                    "Don't use default SSLContext "
                    "with custom poolmanager kwargs"
                ),
                "ref_items": [],
            }
        ]

        result = evaluate_strengthening(
            claim,
            timeline,
        )

        self.assertEqual(
            result,
            STRENGTHENABLE,
        )

    def test_historical_event_cannot_strengthen_current_behavior(self):
        claim = self.make_behavior(
            "Added code: current_behavior()",
            source_event="old111",
        )

        timeline = [
            {
                "hash": "old111",
                "message": "Current behavior",
                "ref_items": [],
            },
            {
                "hash": "new222",
                "message": "Different final behavior",
                "ref_items": [],
            },
        ]

        result = evaluate_strengthening(
            claim,
            timeline,
        )

        self.assertEqual(
            result,
            KEEP_RAW,
        )

    def test_unrelated_evidence_keeps_raw_behavior(self):
        claim = self.make_behavior(
            "Added code: validate_payment(order)"
        )

        timeline = [
            {
                "hash": "final123",
                "message": "Improve image rendering",
                "ref_items": [
                    {
                        "status": "SUCCESS",
                        "type": "PR",
                        "number": 10,
                        "title": "Optimize image thumbnails",
                        "body": "",
                    }
                ],
            }
        ]

        result = evaluate_strengthening(
            claim,
            timeline,
        )

        self.assertEqual(
            result,
            KEEP_RAW,
        )

    def test_successful_pr_context_can_support_agreement(self):
        claim = self.make_behavior(
            'Added code: o = o.encode("utf-8")'
        )

        timeline = [
            {
                "hash": "final123",
                "message": "",
                "ref_items": [
                    {
                        "status": "SUCCESS",
                        "type": "PR",
                        "number": 6589,
                        "title": "Count encoded bytes for str",
                        "body": (
                            "Encode string input as utf-8 "
                            "before measuring its length."
                        ),
                    }
                ],
            }
        ]

        result = evaluate_strengthening(
            claim,
            timeline,
        )

        self.assertEqual(
            result,
            STRENGTHENABLE,
        )

    def test_not_found_reference_is_not_strengthening_evidence(self):
        claim = self.make_behavior(
            'Added code: o = o.encode("utf-8")'
        )

        timeline = [
            {
                "hash": "final123",
                "message": "",
                "ref_items": [
                    {
                        "status": "NOT_FOUND",
                        "type": "PR",
                        "number": 6589,
                        "title": "Count encoded bytes for str",
                        "body": "Encode string input as utf-8.",
                    }
                ],
            }
        ]

        result = evaluate_strengthening(
            claim,
            timeline,
        )

        self.assertEqual(
            result,
            KEEP_RAW,
        )

    def test_non_target_relevant_claim_cannot_strengthen(self):
        claim = self.make_behavior(
            "Added code: current_behavior()"
        )

        claim["target_relevant"] = False

        timeline = [
            {
                "hash": "final123",
                "message": "Current behavior",
                "ref_items": [],
            }
        ]

        result = evaluate_strengthening(
            claim,
            timeline,
        )

        self.assertEqual(
            result,
            KEEP_RAW,
        )

    def test_collect_strengthenable_claims_filters_raw_claims(self):
        matching = self.make_behavior(
            "Added code: ssl_context = custom_context"
        )

        unrelated = self.make_behavior(
            "Added code: render_thumbnail(image)"
        )

        timeline = [
            {
                "hash": "final123",
                "message": (
                    "Preserve custom ssl_context "
                    "configuration"
                ),
                "ref_items": [],
            }
        ]

        result = collect_strengthenable_claims(
            [
                matching,
                unrelated,
            ],
            timeline,
        )

        self.assertEqual(
            len(result),
            1,
        )

        self.assertIn(
            "ssl_context",
            result[0]["text"],
        )

        self.assertEqual(
            result[0]["strengthening"],
            STRENGTHENABLE,
        )


if __name__ == "__main__":
    unittest.main()