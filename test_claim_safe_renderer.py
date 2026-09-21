import unittest

from claim_safe_renderer import (
    render_safe_semantics,
    render_safe_semantics_list,
)
from claim_safety import (
    BLOCK,
    SAFE_TO_RENDER,
)
from claim_semantics import (
    make_behavior_semantics,
)


class TestClaimSafeRenderer(unittest.TestCase):

    def make_safe(
        self,
        **kwargs,
    ):
        semantics = make_behavior_semantics(
            **kwargs
        )

        semantics["semantic_safety"] = (
            SAFE_TO_RENDER
        )

        return semantics

    def test_encode_template(self):
        semantics = self.make_safe(
            action="ENCODE",
            subject="string input",
            target="UTF-8",
            source_event="abc123",
        )

        result = render_safe_semantics(
            semantics
        )

        self.assertEqual(
            result,
            "string input is encoded as UTF-8.",
        )

    def test_encode_with_direct_condition_template(self):
        semantics = self.make_safe(
            action="ENCODE",
            subject="string input",
            condition="the input is a string",
            target="UTF-8",
            source_event="abc123",
        )

        result = render_safe_semantics(
            semantics
        )

        self.assertEqual(
            result,
            (
                "string input is encoded as UTF-8 "
                "when the input is a string."
            ),
        )

    def test_avoid_template(self):
        semantics = self.make_safe(
            action="AVOID",
            subject="default SSLContext",
            condition="custom SSLContext exists",
            source_event="abc123",
        )

        result = render_safe_semantics(
            semantics
        )

        self.assertEqual(
            result,
            (
                "default SSLContext is not used "
                "when custom SSLContext exists."
            ),
        )

    def test_blocked_semantics_are_not_rendered(self):
        semantics = make_behavior_semantics(
            action="AVOID",
            subject="default SSLContext",
            condition="custom SSLContext exists",
            source_event="abc123",
        )

        semantics["semantic_safety"] = BLOCK

        result = render_safe_semantics(
            semantics
        )

        self.assertIsNone(
            result
        )

    def test_missing_required_field_is_not_inferred(self):
        semantics = self.make_safe(
            action="ENCODE",
            subject="string input",
            source_event="abc123",
        )

        result = render_safe_semantics(
            semantics
        )

        self.assertIsNone(
            result
        )

    def test_unknown_action_is_not_rendered(self):
        semantics = self.make_safe(
            action="OPTIMIZE",
            subject="request",
            source_event="abc123",
        )

        result = render_safe_semantics(
            semantics
        )

        self.assertIsNone(
            result
        )

    def test_renderer_does_not_invent_reason(self):
        semantics = self.make_safe(
            action="ENCODE",
            subject="string input",
            target="UTF-8",
            source_event="abc123",
        )

        result = render_safe_semantics(
            semantics
        )

        lowered = result.lower()

        for forbidden in (
            "performance",
            "security",
            "because",
            "in order to",
            "fix",
        ):
            self.assertNotIn(
                forbidden,
                lowered,
            )

    def test_safe_list_filters_unrenderable_items(self):
        safe = self.make_safe(
            action="ADD",
            subject="validation check",
            source_event="abc123",
        )

        unsupported = self.make_safe(
            action="OPTIMIZE",
            subject="request",
            source_event="abc123",
        )

        blocked = make_behavior_semantics(
            action="REMOVE",
            subject="validation check",
            source_event="abc123",
        )

        blocked["semantic_safety"] = BLOCK

        result = render_safe_semantics_list(
            [
                safe,
                unsupported,
                blocked,
            ]
        )

        self.assertEqual(
            result,
            [
                "validation check is added.",
            ],
        )


if __name__ == "__main__":
    unittest.main()