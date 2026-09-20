import unittest

from narrative import append_supported_claims


class TestClaimNarrative(unittest.TestCase):

    def test_high_confidence_supported_behavior_is_appended(self):
        timeline = [
            {
                "hash": "old1234",
                "type": "FIRST OBSERVED",
                "diff_lines": [],
                "ref_items": [],
            },
            {
                "hash": "3fd309a5",
                "type": "BUG FIX",
                "diff_lines": [
                    "+ if isinstance(o, str):",
                    '+ o = o.encode("utf-8")',
                ],
                "ref_items": [],
            },
        ]

        stats = {
            "confidence": "VERY HIGH",
            "consistency": "HIGH",
            "is_blocked": False,
        }

        result = append_supported_claims(
            "Base narrative.",
            timeline,
            stats,
        )

        self.assertIn(
            "o is encoded as UTF-8.",
            result,
        )

        self.assertNotIn(
            "performance",
            result.lower(),
        )

    def test_inconsistent_pipeline_does_not_append_claim(self):
        timeline = [
            {
                "hash": "old1234",
                "type": "FIRST OBSERVED",
                "diff_lines": [],
                "ref_items": [],
            },
            {
                "hash": "3fd309a5",
                "type": "BUG FIX",
                "diff_lines": [
                    '+ o = o.encode("utf-8")',
                ],
                "ref_items": [],
            },
        ]

        stats = {
            "confidence": "VERY HIGH",
            "consistency": "INCONSISTENT",
            "is_blocked": True,
        }

        result = append_supported_claims(
            "Base narrative.",
            timeline,
            stats,
        )

        self.assertEqual(
            result,
            "Base narrative.",
        )

    def test_low_confidence_does_not_append_claim(self):
        timeline = [
            {
                "hash": "old1234",
                "type": "FIRST OBSERVED",
                "diff_lines": [],
                "ref_items": [],
            },
            {
                "hash": "3fd309a5",
                "type": "BUG FIX",
                "diff_lines": [
                    '+ o = o.encode("utf-8")',
                ],
                "ref_items": [],
            },
        ]

        stats = {
            "confidence": "LOW",
            "consistency": "HIGH",
            "is_blocked": False,
        }

        result = append_supported_claims(
            "Base narrative.",
            timeline,
            stats,
        )

        self.assertEqual(
            result,
            "Base narrative.",
        )

    def test_medium_confidence_uses_conservative_label(self):
        timeline = [
            {
                "hash": "old1234",
                "type": "FIRST OBSERVED",
                "diff_lines": [],
                "ref_items": [],
            },
            {
                "hash": "3fd309a5",
                "type": "BUG FIX",
                "diff_lines": [
                    '+ o = o.encode("utf-8")',
                ],
                "ref_items": [],
            },
        ]

        stats = {
            "confidence": "MEDIUM",
            "consistency": "HIGH",
            "is_blocked": False,
        }

        result = append_supported_claims(
            "Base narrative.",
            timeline,
            stats,
        )

        self.assertIn(
            "확인된 이력 범위에서 관찰되는 코드 동작:",
            result,
        )

        self.assertIn(
            "o is encoded as UTF-8.",
            result,
        )


    def test_medium_confidence_does_not_expose_pr_cause_claim(self):
        timeline = [
            {
                "hash": "medium001",
                "type": "FIRST OBSERVED",
                "diff_lines": [],
                "ref_items": [],
            },
            {
                "hash": "medium002",
                "type": "BUG FIX",
                "diff_lines": [],
                "ref_items": [
                    {
                        "status": "SUCCESS",
                        "type": "PR",
                        "number": 501,
                        "title": "Prevent double charge",
                    }
                ],
            },
        ]

        stats = {
            "confidence": "MEDIUM",
            "consistency": "HIGH",
            "is_blocked": False,
        }

        result = append_supported_claims(
            "Base narrative.",
            timeline,
            stats,
        )

        self.assertNotIn(
            "PR #501",
            result,
        )

        self.assertNotIn(
            "Prevent double charge",
            result,
        )


if __name__ == "__main__":
    unittest.main()