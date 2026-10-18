import unittest
from unittest.mock import patch

from beginner_behavior_adapter import (
    build_beginner_behavior_from_analysis,
)
from webapp.beginner_behavior import BehaviorStatus


class BeginnerBehaviorAdapterTests(unittest.TestCase):
    def make_semantic(self):
        return {
            "action": "USE",
            "subject": "value",
            "target": "result",
            "field_evidence": {
                "action": [
                    {"level": "DIRECT", "code_excerpt": "value"}
                ],
                "subject": [
                    {"level": "DIRECT", "code_excerpt": "value"}
                ],
                "target": [
                    {"level": "DIRECT", "code_excerpt": "value"}
                ],
            },
        }

    def test_adapter_uses_existing_behavior_claims(self):
        claim = {
            "type": "BEHAVIOR",
            "target_relevant": True,
            "source_event": "event-1",
            "evidence": [],
            "structured_semantics": [self.make_semantic()],
        }

        with patch(
            "beginner_behavior_adapter.build_behavior_claims",
            return_value=[claim],
        ) as mocked:
            build_beginner_behavior_from_analysis(
                ["value"],
                ["value"],
                {},
            )

        mocked.assert_called_once_with(["value"])

    def test_unsafe_semantic_has_no_step(self):
        semantic = self.make_semantic()
        semantic["field_evidence"]["action"][0]["level"] = "PARTIAL"
        claim = {
            "type": "BEHAVIOR",
            "target_relevant": True,
            "structured_semantics": [semantic],
        }

        result = build_beginner_behavior_from_claims(
            [claim],
            ["value"],
        )

        self.assertIs(result.status, BehaviorStatus.WITHHELD)

    def test_safe_statement_comes_from_existing_renderer(self):
        semantic = self.make_semantic()
        claim = {
            "type": "BEHAVIOR",
            "target_relevant": True,
            "structured_semantics": [semantic],
        }

        with patch(
            "beginner_behavior_adapter.render_safe_semantics",
            return_value="value is used for result.",
        ) as renderer:
            result = build_beginner_behavior_from_claims(
                [claim],
                ["value"],
            )

        renderer.assert_called_once()
        self.assertEqual(
            result.steps[0].statement,
            "value is used for result.",
        )
        self.assertTrue(result.steps[0].is_directly_observed)

    def test_diff_fallback_is_not_used(self):
        claim = {
            "type": "BEHAVIOR",
            "target_relevant": True,
            "text": "Added code: value",
            "structured_semantics": [],
        }

        result = build_beginner_behavior_from_claims(
            [claim],
            ["value"],
        )

        self.assertIs(result.status, BehaviorStatus.NOT_ESTABLISHED)

    def test_external_text_is_not_behavior_evidence(self):
        semantic = self.make_semantic()
        semantic["field_evidence"]["action"][0]["source"] = "PR"
        claim = {
            "type": "BEHAVIOR",
            "target_relevant": True,
            "structured_semantics": [semantic],
        }

        result = build_beginner_behavior_from_claims(
            [claim],
            ["value"],
        )

        self.assertIs(result.status, BehaviorStatus.NOT_ESTABLISHED)

    def test_confidence_does_not_change_behavior_result(self):
        claim = {
            "type": "BEHAVIOR",
            "target_relevant": True,
            "structured_semantics": [self.make_semantic()],
        }

        results = [
            build_beginner_behavior_from_claims(
                [claim],
                ["value"],
                {"confidence": confidence},
            ).status
            for confidence in ("HIGH", "WEAK")
        ]

        self.assertEqual(results[0], results[1])

    def test_blocked_and_inconsistent_inputs_withhold(self):
        claim = {
            "type": "BEHAVIOR",
            "target_relevant": True,
            "structured_semantics": [self.make_semantic()],
        }

        blocked = build_beginner_behavior_from_claims(
            [claim],
            ["value"],
            {"is_blocked": True},
        )
        inconsistent = build_beginner_behavior_from_claims(
            [claim],
            ["value"],
            {"consistency": "INCONSISTENT"},
        )

        self.assertIs(blocked.status, BehaviorStatus.WITHHELD)
        self.assertIs(
            inconsistent.status,
            BehaviorStatus.WITHHELD,
        )

    def test_no_claims_are_not_established(self):
        result = build_beginner_behavior_from_claims([], ["value"])

        self.assertIs(result.status, BehaviorStatus.NOT_ESTABLISHED)


def build_beginner_behavior_from_claims(
    claims,
    current_lines,
    stats=None,
):
    with patch(
        "beginner_behavior_adapter.build_behavior_claims",
        return_value=claims,
    ):
        return build_beginner_behavior_from_analysis(
            [],
            current_lines,
            stats or {},
        )


if __name__ == "__main__":
    unittest.main()
