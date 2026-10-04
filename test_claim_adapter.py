import unittest

from claim_adapter import (
    build_behavior_claims,
    build_candidate_claims,
    build_reference_claims,
    build_revert_claims,
    select_target_behavior_events,
)
from claim_evidence import (
    BEHAVIOR,
    CAUSE,
    REVERT_FACT,
    SUPPORTED,
    UNVERIFIED,
    collect_supported_claims,
    evaluate_claim,
    make_claim,
)


class TestClaimAdapter(unittest.TestCase):

    def test_added_diff_creates_behavior_claim(self):
        timeline = [
            {
                "hash": "abc1234",
                "diff_lines": [
                    '+ o = o.encode("utf-8")',
                ],
                "ref_items": [],
                "type": "BUG FIX",
            }
        ]

        claims = build_behavior_claims(timeline)

        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["type"], BEHAVIOR)
        self.assertIn(
            'o = o.encode("utf-8")',
            claims[0]["text"],
        )

    def test_deleted_diff_does_not_create_behavior_claim(self):
        timeline = [
            {
                "hash": "abc1234",
                "diff_lines": [
                    "- old_behavior()",
                ],
                "ref_items": [],
                "type": "BUG FIX",
            }
        ]

        claims = build_behavior_claims(timeline)

        self.assertEqual(claims, [])

    def test_successful_pr_creates_reference_claim(self):
        timeline = [
            {
                "hash": "abc1234",
                "diff_lines": [],
                "type": "BUG FIX",
                "ref_items": [
                    {
                        "status": "SUCCESS",
                        "type": "PR",
                        "number": 6589,
                        "title": (
                            "Enhance super_len to "
                            "count encoded bytes for str"
                        ),
                    }
                ],
            }
        ]

        claims = build_reference_claims(timeline)

        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["type"], CAUSE)
        self.assertIn(
            "PR #6589",
            claims[0]["text"],
        )

    def test_not_found_reference_does_not_create_claim(self):
        timeline = [
            {
                "hash": "abc1234",
                "diff_lines": [],
                "type": "BUG FIX",
                "ref_items": [
                    {
                        "status": "NOT_FOUND",
                        "type": "UNKNOWN",
                        "number": 999,
                        "title": "",
                    }
                ],
            }
        ]

        claims = build_reference_claims(timeline)

        self.assertEqual(claims, [])

    def test_revert_event_creates_revert_fact(self):
        timeline = [
            {
                "hash": "bb7be1f6",
                "diff_lines": [],
                "ref_items": [],
                "type": "REVERT",
            }
        ]

        claims = build_revert_claims(timeline)

        self.assertEqual(len(claims), 1)
        self.assertEqual(
            claims[0]["type"],
            REVERT_FACT,
        )

    def test_candidate_claims_can_flow_to_supported_filter(self):
        timeline = [
            {
                "hash": "3fd309a",
                "diff_lines": [
                    '+ o = o.encode("utf-8")',
                ],
                "type": "BUG FIX",
                "ref_items": [],
            }
        ]

        claims = build_candidate_claims(timeline)
        supported = collect_supported_claims(claims)

        self.assertEqual(len(supported), 1)
        self.assertEqual(
            supported[0]["status"],
            SUPPORTED,
        )
        self.assertEqual(
            supported[0]["type"],
            BEHAVIOR,
        )

    def test_requests_002_behavior_is_recovered_as_supported(self):
        timeline = [
            {
                "hash": "3fd309a5",
                "diff_lines": [
                    "+ if isinstance(o, str):",
                    '+ o = o.encode("utf-8")',
                ],
                "type": "BUG FIX",
                "ref_items": [
                    {
                        "status": "SUCCESS",
                        "type": "PR",
                        "number": 6589,
                        "title": (
                            "Enhance super_len to "
                            "count encoded bytes for str"
                        ),
                    }
                ],
            }
        ]

        claims = build_candidate_claims(timeline)
        supported = collect_supported_claims(claims)

        behavior_claims = [
            claim
            for claim in supported
            if claim["type"] == BEHAVIOR
        ]

        self.assertEqual(
            len(behavior_claims),
            2,
        )

        texts = [
            claim["text"]
            for claim in behavior_claims
        ]

        self.assertTrue(
            any(
                'o = o.encode("utf-8")' in text
                for text in texts
            )
        )

    def test_requests_002_unsupported_performance_cause_stays_unverified(self):
        claim = make_claim(
            "The change was made to improve performance.",
            CAUSE,
            [],
        )

        result = evaluate_claim(claim)

        self.assertEqual(
            result["status"],
            UNVERIFIED,
        )

    def test_target_behavior_uses_only_final_event(self):
        timeline = [
            {
                "hash": "old1111",
                "diff_lines": [
                    "+ old_behavior()",
                ],
                "ref_items": [],
                "type": "FIRST OBSERVED",
            },
            {
                "hash": "new2222",
                "diff_lines": [
                    "+ current_behavior()",
                ],
                "ref_items": [],
                "type": "UPDATE",
            },
        ]

        claims = build_behavior_claims(timeline)

        self.assertEqual(
            len(claims),
            1,
        )

        self.assertIn(
            "current_behavior()",
            claims[0]["text"],
        )

        self.assertNotIn(
            "old_behavior()",
            claims[0]["text"],
        )

        self.assertEqual(
            claims[0]["source_event"],
            "new2222",
        )

        self.assertTrue(
            claims[0]["target_relevant"],
        )

    def test_historical_added_lines_are_not_current_behavior(self):
        timeline = [
            {
                "hash": "c0813a2",
                "diff_lines": [
                    "+ if isinstance(verify, str):",
                    '+ pool_kwargs["ca_certs"] = verify',
                ],
                "ref_items": [],
                "type": "FIRST OBSERVED",
            },
            {
                "hash": "9a40d12",
                "diff_lines": [
                    "- if isinstance(verify, str):",
                    '- pool_kwargs["ca_certs"] = verify',
                    "+ elif verify is True:",
                    '+ pool_kwargs["ssl_context"] = _preloaded_ssl_context',
                ],
                "ref_items": [],
                "type": "UPDATE",
            },
            {
                "hash": "b1d73dd",
                "diff_lines": [
                    "- elif verify is True:",
                    (
                        "+ elif verify is True and not "
                        "has_poolmanager_ssl_context:"
                    ),
                ],
                "ref_items": [],
                "type": "UPDATE",
            },
        ]

        claims = build_behavior_claims(timeline)

        texts = [
            claim["text"]
            for claim in claims
        ]

        self.assertEqual(
            len(texts),
            1,
        )

        self.assertIn(
            "has_poolmanager_ssl_context",
            texts[0],
        )

        self.assertTrue(
            all(
                "ca_certs" not in text
                for text in texts
            )
        )

        self.assertTrue(
            all(
                'pool_kwargs["ssl_context"]'
                not in text
                for text in texts
            )
        )

    def test_single_event_remains_target_behavior_source(self):
        timeline = [
            {
                "hash": "3fd309a5",
                "diff_lines": [
                    "+ if isinstance(o, str):",
                    '+ o = o.encode("utf-8")',
                ],
                "ref_items": [],
                "type": "FIRST OBSERVED",
            }
        ]

        events = select_target_behavior_events(
            timeline
        )

        self.assertEqual(
            len(events),
            1,
        )

        self.assertEqual(
            events[0]["hash"],
            "3fd309a5",
        )

        claims = build_behavior_claims(
            timeline
        )

        self.assertEqual(
            len(claims),
            2,
        )

    def test_empty_timeline_has_no_target_behavior_event(self):
        events = select_target_behavior_events([])

        self.assertEqual(
            events,
            [],
        )

        claims = build_behavior_claims([])

        self.assertEqual(
            claims,
            [],
        )


if __name__ == "__main__":
    unittest.main()