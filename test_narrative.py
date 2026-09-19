import unittest
from narrative import synthesize_narrative


class TestNarrative(unittest.TestCase):

    def test_single_commit_origin_narrative(self):
        timeline = [
            {
                "date": "2026-09-01",
                "hash": "c1a2b3c",
                "message": "feat: initial service",
                "ref_items": []
            }
        ]

        headline, body = synthesize_narrative(timeline, {})

        self.assertTrue(headline)
        self.assertTrue(body)
        self.assertIn("c1a2b3c", body)

    def test_revert_recovery_narrative(self):
        timeline = [
            {
                "date": "2026-01-01",
                "hash": "a111",
                "message": "feat: init",
                "is_revert": False,
                "type": "FIRST OBSERVED"
            },
            {
                "date": "2026-01-02",
                "hash": "a222",
                "message": "revert: rollback bad commit",
                "is_revert": True,
                "type": "REVERT"
            },
            {
                "date": "2026-01-03",
                "hash": "a333",
                "message": "fix: safe recovery",
                "is_revert": False,
                "type": "BUG FIX",
                "ref_items": [
                    {
                        "number": 105,
                        "type": "PR",
                        "title": "Safe null check"
                    }
                ]
            }
        ]

        headline, body = synthesize_narrative(timeline, {})

        self.assertIn("롤백", headline)
        self.assertIn("a222", body)
        self.assertIn("PR #105", body)
        self.assertIn("a333", body)

    def test_evolution_bug_fix_narrative(self):
        timeline = [
            {
                "date": "2026-01-01",
                "hash": "b111",
                "message": "feat: init",
                "is_revert": False,
                "type": "FIRST OBSERVED"
            },
            {
                "date": "2026-01-02",
                "hash": "b222",
                "message": "fix: prevent race",
                "is_revert": False,
                "type": "BUG FIX",
                "ref_items": [
                    {
                        "number": 200,
                        "type": "PR",
                        "title": "Race condition"
                    }
                ]
            }
        ]

        headline, body = synthesize_narrative(timeline, {})

        self.assertTrue(headline)
        self.assertIn("b222", body)
        self.assertIn("PR #200", body)

    def test_complex_multi_event_narrative(self):
        timeline = [
            {
                "date": "2026-01-01",
                "hash": "7c4ff0",
                "type": "FIRST OBSERVED",
                "message": "feat: initial payment"
            },
            {
                "date": "2026-01-02",
                "hash": "2c17f74",
                "type": "BUG FIX",
                "message": "fix: check null"
            },
            {
                "date": "2026-01-03",
                "hash": "2f467c3",
                "type": "BUG FIX",
                "message": "fix: prevent race condition"
            },
            {
                "date": "2026-01-04",
                "hash": "8857c0c",
                "type": "REVERT",
                "message": "revert: rollback temporary condition",
                "is_revert": True
            },
            {
                "date": "2026-01-05",
                "hash": "887d17e",
                "type": "FEATURE",
                "message": "feat: add status check"
            },
            {
                "date": "2026-01-06",
                "hash": "f50e0a1",
                "type": "UPDATE",
                "message": "test: verify why-blame PR integration",
                "ref_items": [
                    {
                        "number": 1,
                        "type": "PR",
                        "title": "test: verify why-blame PR integration"
                    }
                ]
            }
        ]

        headline, body = synthesize_narrative(timeline, {})

        self.assertTrue(headline)
        self.assertIn("2c17f74", body)
        self.assertIn("2f467c3", body)
        self.assertIn("8857c0c", body)
        self.assertIn("887d17e", body)
        self.assertIn("PR #1", body)
        self.assertNotIn("side effect", body.lower())

    def test_blocked_confidence_prevents_specific_why(self):
        timeline = [
            {
                "date": "2026-09-01",
                "hash": "blocked01",
                "message": "fix: payment condition",
                "type": "BUG FIX",
                "ref_items": []
            },
            {
                "date": "2026-09-02",
                "hash": "blocked02",
                "message": "update: payment flow",
                "type": "UPDATE",
                "ref_items": []
            }
        ]

        stats = {
            "consistency": "MODERATE",
            "is_blocked": True,
            "inconsistent_pairs": []
        }

        headline, body = synthesize_narrative(timeline, stats)

        self.assertTrue(headline)
        self.assertTrue(body)
        self.assertNotIn("payment flow", body)

    def test_unverified_cause_is_not_presented_as_why(self):
        timeline = [
            {
                "date": "2026-09-18",
                "hash": "abc123",
                "message": "feat: initial payment flow",
                "type": "FEATURE",
                "is_revert": False,
            },
            {
                "date": "2026-09-19",
                "hash": "def456",
                "message": "fix double charge and improve performance",
                "type": "FEATURE",
                "is_revert": False,
                "ref_items": [
                    {
                        "number": 123,
                        "type": "PR",
                        "title": "Fix double charge",
                    }
                ],
            },
        ]

        stats = {
            "score": 5,
            "consistency": "HIGH",
            "is_blocked": False,
        }

        headline, body = synthesize_narrative(timeline, stats)

        self.assertIn("double charge", body)
        self.assertNotIn("improve performance", body)

    def test_moderate_confidence_does_not_assert_unverified_final_cause(self):
        timeline = [
            {
                "date": "2026-09-19",
                "hash": "abc123",
                "message": "fix: payment validation",
                "type": "BUG FIX",
                "is_revert": False,
                "ref_items": [
                    {
                        "number": 123,
                        "type": "PR",
                        "title": "Payment validation",
                    }
                ],
            },
            {
                "date": "2026-09-19",
                "hash": "def456",
                "message": "fix: handle edge case",
                "type": "BUG FIX",
                "is_revert": False,
                "ref_items": [],
            },
        ]

        stats = {
            "score": 4,
            "availability": "MODERATE",
            "consistency": "HIGH",
            "source_reliability": "MODERATE",
            "history_ambiguity": "LOW",
            "overall_confidence": "MODERATE",
            "is_blocked": False,
        }

        headline, body = synthesize_narrative(timeline, stats)

        self.assertNotIn("handle edge case", body)


if __name__ == "__main__":
    unittest.main()