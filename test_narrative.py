import unittest

from narrative import synthesize_narrative


class TestNarrative(unittest.TestCase):

    def test_single_commit_origin_narrative(self):
        timeline = [
            {
                "date": "2026-09-01",
                "hash": "c1a2b3c",
                "message": "feat: initial service",
                "ref_items": [],
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
                "type": "FIRST OBSERVED",
            },
            {
                "date": "2026-01-02",
                "hash": "a222",
                "message": "revert: rollback bad commit",
                "is_revert": True,
                "type": "REVERT",
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
                        "title": "Safe null check",
                    }
                ],
            },
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
                "type": "FIRST OBSERVED",
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
                        "title": "Race condition",
                    }
                ],
            },
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
                "message": "feat: initial payment",
            },
            {
                "date": "2026-01-02",
                "hash": "2c17f74",
                "type": "BUG FIX",
                "message": "fix: check null",
            },
            {
                "date": "2026-01-03",
                "hash": "2f467c3",
                "type": "BUG FIX",
                "message": "fix: prevent race condition",
            },
            {
                "date": "2026-01-04",
                "hash": "8857c0c",
                "type": "REVERT",
                "message": "revert: rollback temporary condition",
                "is_revert": True,
            },
            {
                "date": "2026-01-05",
                "hash": "887d17e",
                "type": "FEATURE",
                "message": "feat: add status check",
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
                        "title": "test: verify why-blame PR integration",
                    }
                ],
            },
        ]

        headline, body = synthesize_narrative(timeline, {})

        self.assertTrue(headline)
        self.assertIn("2c17f74", body)
        self.assertIn("2f467c3", body)
        self.assertIn("8857c0c", body)
        self.assertIn("887d17e", body)
        self.assertIn("PR #1", body)

        # Revert가 존재한다는 사실만으로 구체적인 원인을 만들면 안 된다.
        self.assertNotIn("side effect", body.lower())

    def test_blocked_confidence_prevents_specific_why(self):
        timeline = [
            {
                "date": "2026-09-01",
                "hash": "blocked01",
                "message": "fix: payment condition",
                "type": "BUG FIX",
                "ref_items": [],
            },
            {
                "date": "2026-09-02",
                "hash": "blocked02",
                "message": "update: payment flow",
                "type": "UPDATE",
                "ref_items": [],
            },
        ]

        stats = {
            "consistency": "MODERATE",
            "is_blocked": True,
            "inconsistent_pairs": [],
        }

        headline, body = synthesize_narrative(timeline, stats)

        self.assertTrue(headline)
        self.assertTrue(body)

        # Blocked 상태에서는 구체적인 마지막 변경 이유를 WHY로 사용하지 않는다.
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

        # PR에서 확인 가능한 원인은 표현할 수 있다.
        self.assertIn("double charge", body)

        # PR에서 검증되지 않은 performance 원인은 WHY로 확정하면 안 된다.
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

        # Moderate confidence에서는 검증되지 않은 최종 원인을 단정하지 않는다.
        self.assertNotIn("handle edge case", body)

    def test_narrative_avoids_unsupported_evaluative_language(self):
        """
        Git 이력에서 직접 확인할 수 없는 평가적 표현이
        Narrative에 다시 들어오는 것을 방지한다.

        REVERT가 있다는 것은 '롤백이 있었다'는 사실을 의미할 뿐,
        코드가 '방어적', '보강됨', '발전됨'을 증명하지는 않는다.
        """
        timeline = [
            {
                "date": "2026-09-18",
                "hash": "aaa111",
                "message": "feat: initial implementation",
                "type": "FIRST OBSERVED",
                "is_revert": False,
                "ref_items": [],
            },
            {
                "date": "2026-09-19",
                "hash": "bbb222",
                "message": "revert: rollback temporary change",
                "type": "REVERT",
                "is_revert": True,
                "ref_items": [],
            },
            {
                "date": "2026-09-20",
                "hash": "ccc333",
                "message": "fix: update condition",
                "type": "BUG FIX",
                "is_revert": False,
                "ref_items": [],
            },
        ]

        stats = {
            "is_blocked": False,
            "consistency": "UNLINKED",
            "overall_confidence": "MODERATE",
        }

        headline, body = synthesize_narrative(timeline, stats)

        text = f"{headline} {body}"

        # 증거가 직접 뒷받침하지 않는 평가적 표현을 금지한다.
        self.assertNotIn("방어적 코드", text)
        self.assertNotIn("보강된 코드", text)
        self.assertNotIn("발전된 코드", text)

        # Git 이력에서 직접 확인 가능한 사실은 유지한다.
        self.assertIn("롤백(1회)", headline)
        self.assertIn("변경 이력", headline)
        self.assertIn("현재 형태로 정착된 코드", headline)

        # 실제 Revert commit 역시 History 설명에서 보존되어야 한다.
        self.assertIn("bbb222", body)


if __name__ == "__main__":
    unittest.main()