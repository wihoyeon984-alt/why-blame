import unittest

from claim_adapter import build_candidate_claims
from claim_evidence import (
    BEHAVIOR,
    SUPPORTED,
    UNVERIFIED,
    collect_supported_claims,
    make_claim,
)
from claim_renderer import (
    render_behavior_claim,
    render_supported_claims,
)


class TestClaimRenderer(unittest.TestCase):

    def test_utf8_encode_behavior_is_rendered(self):
        claim = make_claim(
            'Added code: o = o.encode("utf-8")',
            BEHAVIOR,
            [],
        )
        claim["status"] = SUPPORTED

        result = render_behavior_claim(
            claim
        )

        self.assertEqual(
            result,
            "o is encoded as UTF-8.",
        )

    def test_isinstance_string_check_is_rendered(self):
        claim = make_claim(
            "Added code: if isinstance(o, str):",
            BEHAVIOR,
            [],
        )
        claim["status"] = SUPPORTED

        result = render_behavior_claim(
            claim
        )

        self.assertEqual(
            result,
            "The code checks whether o is a string.",
        )


    def test_supported_behavior_renders_safe_structured_semantics(self):
        claim = make_claim(
            "Added code: result = helper(item, expected)",
            BEHAVIOR,
            [],
        )
        claim["status"] = SUPPORTED
        claim["structured_semantics"] = [
            {
                "type": "BEHAVIOR",
                "action": "RETURN",
                "subject": None,
                "condition": "co.co_filename == filename",
                "target": "co",
                "scope": None,
                "source_event": "abc123",
                "field_evidence": {
                    "action": [
                        {"source": "DIFF", "ref": "abc123", "level": "DIRECT"}
                    ],
                    "target": [
                        {"source": "DIFF", "ref": "abc123", "level": "DIRECT"}
                    ],
                    "condition": [
                        {"source": "DIFF", "ref": "abc123", "level": "DIRECT"}
                    ],
                },
                "entailment": "NONE",
            }
        ]

        result = render_behavior_claim(claim)

        self.assertEqual(
            result,
            "co is returned when co.co_filename == filename.",
        )


    def test_unsafe_structured_semantics_falls_back_to_original_claim(self):
        original = "Added code: result = helper(item, expected)"

        claim = make_claim(
            original,
            BEHAVIOR,
            [],
        )
        claim["status"] = SUPPORTED
        claim["structured_semantics"] = [
            {
                "type": "BEHAVIOR",
                "action": "RETURN",
                "subject": None,
                "condition": "co.co_filename == filename",
                "target": "co",
                "scope": None,
                "source_event": "abc123",
                "field_evidence": {},
                "entailment": "NONE",
            }
        ]

        result = render_behavior_claim(claim)

        self.assertEqual(
            result,
            original,
        )

    def test_unknown_behavior_falls_back_to_original_claim(self):
        original = "Added code: custom_operation(value)"

        claim = make_claim(
            original,
            BEHAVIOR,
            [],
        )
        claim["status"] = SUPPORTED

        result = render_behavior_claim(
            claim
        )

        self.assertEqual(
            result,
            original,
        )

    def test_unverified_claim_is_not_transformed(self):
        original = 'Added code: o = o.encode("utf-8")'

        claim = make_claim(
            original,
            BEHAVIOR,
            [],
        )
        claim["status"] = UNVERIFIED

        result = render_behavior_claim(
            claim
        )

        self.assertEqual(
            result,
            original,
        )

    def test_supported_filter_excludes_unverified_claim(self):
        supported = make_claim(
            'Added code: o = o.encode("utf-8")',
            BEHAVIOR,
            [],
        )
        supported["status"] = SUPPORTED

        unverified = make_claim(
            "The change improves performance.",
            BEHAVIOR,
            [],
        )
        unverified["status"] = UNVERIFIED

        result = render_supported_claims(
            [
                supported,
                unverified,
            ]
        )

        self.assertEqual(
            result,
            [
                "o is encoded as UTF-8.",
            ],
        )

    def test_requests_002_pipeline_renders_supported_behavior(self):
        timeline = [
            {
                "hash": "3fd309a5",
                "diff_lines": [
                    "+ if isinstance(o, str):",
                    '+ o = o.encode("utf-8")',
                ],
                "type": "BUG FIX",
                "ref_items": [],
            }
        ]

        candidates = build_candidate_claims(
            timeline
        )

        supported = collect_supported_claims(
            candidates
        )

        rendered = render_supported_claims(
            supported
        )

        self.assertIn(
            "o is encoded as UTF-8.",
            rendered,
        )

        self.assertIn(
            "The code checks whether o is a string.",
            rendered,
        )

        self.assertTrue(
            all(
                "performance" not in text.lower()
                for text in rendered
            )
        )


if __name__ == "__main__":
    unittest.main()
