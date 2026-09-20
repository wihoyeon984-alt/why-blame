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

        stats = {
            "confidence": "HIGH",
            "consistency": "HIGH",
            "is_blocked": False,
        }

        headline, body = synthesize_narrative(timeline, stats)

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

        stats = {
            "confidence": "HIGH",
            "consistency": "HIGH",
            "is_blocked": False,
        }

        headline, body = synthesize_narrative(timeline, stats)

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

        stats = {
            "confidence": "HIGH",
            "consistency": "HIGH",
            "is_blocked": False,
        }

        headline, body = synthesize_narrative(timeline, stats)

        self.assertTrue(headline)
        self.assertIn("2c17f74", body)
        self.assertIn("2f467c3", body)
        self.assertIn("8857c0c", body)
        self.assertIn("887d17e", body)
        self.assertIn("PR #1", body)

        # Revert媛 議댁옱?쒕떎???ъ떎留뚯쑝濡?援ъ껜?곸씤 ?먯씤??留뚮뱾硫????쒕떎.
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

        # Blocked ?곹깭?먯꽌??援ъ껜?곸씤 留덉?留?蹂寃??댁쑀瑜?WHY濡??ъ슜?섏? ?딅뒗??
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
            "score": 8,
            "confidence": "HIGH",
            "consistency": "HIGH",
            "is_blocked": False,
        }

        headline, body = synthesize_narrative(timeline, stats)

        # PR?먯꽌 ?뺤씤 媛?ν븳 ?먯씤? ?쒗쁽?????덈떎.
        self.assertIn("double charge", body)

        # PR?먯꽌 寃利앸릺吏 ?딆? performance ?먯씤? WHY濡??뺤젙?섎㈃ ???쒕떎.
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

        # Moderate confidence?먯꽌??寃利앸릺吏 ?딆? 理쒖쥌 ?먯씤???⑥젙?섏? ?딅뒗??
        self.assertNotIn("handle edge case", body)

    def test_narrative_avoids_unsupported_evaluative_language(self):
        """
        Git ?대젰?먯꽌 吏곸젒 ?뺤씤?????녿뒗 ?됯????쒗쁽??        Narrative???ㅼ떆 ?ㅼ뼱?ㅻ뒗 寃껋쓣 諛⑹??쒕떎.

        REVERT媛 ?덈떎??寃껋? '濡ㅻ갚???덉뿀?????ъ떎???섎???肉?
        肄붾뱶媛 '諛⑹뼱??, '蹂닿컯??, '諛쒖쟾????利앸챸?섏????딅뒗??
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

        # 利앷굅媛 吏곸젒 ?룸컺移⑦븯吏 ?딅뒗 ?됯????쒗쁽??湲덉??쒕떎.
        self.assertNotIn("諛⑹뼱??肄붾뱶", text)
        self.assertNotIn("蹂닿컯??肄붾뱶", text)
        self.assertNotIn("諛쒖쟾??肄붾뱶", text)

        # Git ?대젰?먯꽌 吏곸젒 ?뺤씤 媛?ν븳 ?ъ떎? ?좎??쒕떎.
        self.assertIn("롤백(1회)", headline)
        self.assertIn("변경 이력", headline)
        self.assertIn("현재 형태에 이른 코드", headline)

        # ?ㅼ젣 Revert commit ??떆 History ?ㅻ챸?먯꽌 蹂댁〈?섏뼱???쒕떎.
        self.assertIn("bbb222", body)



    # ---------------------------------------------------------
    # Confidence -> Narrative Policy regression tests
    # ---------------------------------------------------------

    def test_confidence_normalization(self):
        from narrative import normalize_confidence

        self.assertEqual(
            normalize_confidence({"confidence": "VERY HIGH"}),
            "VERY_HIGH",
        )
        self.assertEqual(
            normalize_confidence({"confidence": "HIGH"}),
            "HIGH",
        )
        self.assertEqual(
            normalize_confidence({"confidence": "MEDIUM"}),
            "MODERATE",
        )
        self.assertEqual(
            normalize_confidence({"confidence": "MODERATE"}),
            "MODERATE",
        )
        self.assertEqual(
            normalize_confidence({"confidence": "WEAK"}),
            "WEAK",
        )
        self.assertEqual(
            normalize_confidence({"confidence": "LOW"}),
            "LOW",
        )

    def test_missing_confidence_defaults_to_conservative(self):
        from narrative import get_narrative_policy

        self.assertEqual(
            get_narrative_policy({}),
            "CONSERVATIVE",
        )

    def test_high_confidence_allows_verified_reference(self):
        timeline = [
            {
                "date": "2026-09-18",
                "hash": "high001",
                "message": "feat: initial payment flow",
                "type": "FIRST OBSERVED",
                "is_revert": False,
                "ref_items": [],
            },
            {
                "date": "2026-09-19",
                "hash": "high002",
                "message": "fix: prevent double charge",
                "type": "BUG FIX",
                "is_revert": False,
                "ref_items": [
                    {
                        "number": 500,
                        "type": "PR",
                        "title": "Prevent double charge",
                        "status": "SUCCESS",
                    }
                ],
            },
        ]

        stats = {
            "confidence": "HIGH",
            "consistency": "HIGH",
            "is_blocked": False,
        }

        headline, body = synthesize_narrative(timeline, stats)

        self.assertTrue(headline)
        self.assertIn("PR #500", body)
        self.assertIn("Prevent double charge", body)

    def test_medium_confidence_uses_conservative_narrative(self):
        timeline = [
            {
                "date": "2026-09-18",
                "hash": "medium001",
                "message": "feat: initial payment flow",
                "type": "FIRST OBSERVED",
                "is_revert": False,
                "ref_items": [],
            },
            {
                "date": "2026-09-19",
                "hash": "medium002",
                "message": "fix: prevent double charge",
                "type": "BUG FIX",
                "is_revert": False,
                "ref_items": [
                    {
                        "number": 501,
                        "type": "PR",
                        "title": "Prevent double charge",
                        "status": "SUCCESS",
                    }
                ],
            },
        ]

        stats = {
            "confidence": "MEDIUM",
            "consistency": "HIGH",
            "is_blocked": False,
        }

        headline, body = synthesize_narrative(timeline, stats)

        self.assertTrue(headline)
        self.assertNotIn("PR #501", body)
        self.assertNotIn("Prevent double charge", body)
        self.assertIn("변경 이력", body)
        self.assertIn("단정하지 않습니다", body)

    def test_weak_confidence_blocks_specific_why(self):
        timeline = [
            {
                "date": "2026-09-18",
                "hash": "weak001",
                "message": "fix: mysterious production issue",
                "type": "BUG FIX",
                "is_revert": False,
                "ref_items": [],
            },
            {
                "date": "2026-09-19",
                "hash": "weak002",
                "message": "fix: secret root cause",
                "type": "BUG FIX",
                "is_revert": False,
                "ref_items": [],
            },
        ]

        stats = {
            "confidence": "WEAK",
            "consistency": "UNLINKED",
            "is_blocked": False,
        }

        headline, body = synthesize_narrative(timeline, stats)

        self.assertIn(
            "신뢰할 수 있는 변경 사유를 확정하기 어려움",
            headline,
        )
        self.assertIn(
            "구체적인 WHY는 생성하지 않습니다",
            body,
        )

        # Commit message만으로 구체적 원인을 WHY에 재사용하면 안 된다.
        self.assertNotIn("secret root cause", body)

    def test_inconsistent_evidence_always_blocks_why(self):
        timeline = [
            {
                "date": "2026-09-18",
                "hash": "inc001",
                "message": "fix: payment validation",
                "type": "BUG FIX",
                "is_revert": False,
                "ref_items": [
                    {
                        "number": 700,
                        "type": "PR",
                        "title": "Improve image rendering",
                        "status": "SUCCESS",
                    }
                ],
            }
        ]

        stats = {
            # Confidence가 높게 들어오더라도 증거 충돌이 우선한다.
            "confidence": "HIGH",
            "consistency": "INCONSISTENT",
            "is_blocked": True,
            "inconsistent_pairs": [
                "payment validation <-> image rendering"
            ],
        }

        headline, body = synthesize_narrative(timeline, stats)

        self.assertIn("증거 불일치", headline)
        self.assertIn("제시하지 않습니다", body)

        # 충돌한 PR의 내용을 WHY로 채택하면 안 된다.
        self.assertNotIn("Improve image rendering", headline)


if __name__ == "__main__":
    unittest.main()



