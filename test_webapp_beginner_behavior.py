import unittest

from webapp.beginner_behavior import (
    BehaviorStatus,
    build_beginner_behavior_contract,
    validate_beginner_behavior_contract,
)


def semantic(
    excerpt="value = normalize(value)",
    safety="SAFE_TO_RENDER",
    level="DIRECT",
    statement="value is normalized.",
    source="DIFF",
):
    return {
        "action": "USE",
        "subject": "normalize",
        "target": "value",
        "safe_statement": statement,
        "semantic_safety": safety,
        "code_excerpt": excerpt,
        "field_evidence": {
            "action": [
                {
                    "source": source,
                    "level": level,
                    "code_excerpt": excerpt,
                }
            ],
            "subject": [
                {
                    "source": source,
                    "level": level,
                    "code_excerpt": excerpt,
                }
            ],
            "target": [
                {
                    "source": source,
                    "level": level,
                    "code_excerpt": excerpt,
                }
            ],
        },
    }


def claim(semantic_value=None, **overrides):
    result = {
        "type": "BEHAVIOR",
        "target_relevant": True,
        "source_event": "event-1",
        "semantic_safety": "SAFE_TO_RENDER",
        "structured_semantics": [
            semantic_value or semantic()
        ],
    }
    result.update(overrides)
    return result


class BeginnerBehaviorTests(unittest.TestCase):
    def test_exact_current_excerpt_is_directly_observed(self):
        result = build_beginner_behavior_contract(
            ["prefix", "value = normalize(value)", "suffix"],
            [claim()],
            {},
        )

        self.assertIs(
            result.status,
            BehaviorStatus.DIRECTLY_OBSERVED,
        )
        self.assertTrue(result.steps[0].is_directly_observed)

    def test_historical_diff_without_current_excerpt_is_not_established(self):
        result = build_beginner_behavior_contract(
            ["current code"],
            [claim(semantic(excerpt="historical code"))],
            {},
        )

        self.assertIs(result.status, BehaviorStatus.NOT_ESTABLISHED)
        self.assertEqual(result.steps, ())

    def test_non_target_claim_is_not_established(self):
        result = build_beginner_behavior_contract(
            ["value = normalize(value)"],
            [claim(target_relevant=False)],
            {},
        )

        self.assertIs(result.status, BehaviorStatus.NOT_ESTABLISHED)
        self.assertEqual(result.steps, ())

    def test_missing_safe_statement_is_not_established(self):
        value = semantic(statement="")
        result = build_beginner_behavior_contract(
            ["value = normalize(value)"],
            [claim(value)],
            {},
        )

        self.assertIs(result.status, BehaviorStatus.NOT_ESTABLISHED)

    def test_blocked_semantic_is_withheld(self):
        result = build_beginner_behavior_contract(
            ["value = normalize(value)"],
            [claim(semantic(safety="BLOCK"))],
            {},
        )

        self.assertIs(result.status, BehaviorStatus.WITHHELD)
        self.assertEqual(result.steps, ())

    def test_blocked_stats_are_withheld(self):
        result = build_beginner_behavior_contract(
            ["value = normalize(value)"],
            [claim()],
            {"is_blocked": True},
        )

        self.assertIs(result.status, BehaviorStatus.WITHHELD)

    def test_inconsistent_stats_are_withheld(self):
        result = build_beginner_behavior_contract(
            ["value = normalize(value)"],
            [claim()],
            {"consistency": "INCONSISTENT"},
        )

        self.assertIs(result.status, BehaviorStatus.WITHHELD)

    def test_conflicting_field_evidence_is_withheld(self):
        value = semantic()
        value["field_evidence"]["action"].append(
            {"level": "CONFLICTING", "code_excerpt": value["code_excerpt"]}
        )
        result = build_beginner_behavior_contract(
            ["value = normalize(value)"],
            [claim(value)],
            {},
        )

        self.assertIs(result.status, BehaviorStatus.WITHHELD)

    def test_partial_field_evidence_is_partial(self):
        value = semantic(level="PARTIAL")
        result = build_beginner_behavior_contract(
            ["value = normalize(value)"],
            [claim(value)],
            {},
        )

        self.assertIs(result.status, BehaviorStatus.PARTIALLY_OBSERVED)
        self.assertFalse(result.steps[0].is_directly_observed)

    def test_confidence_does_not_change_status(self):
        inputs = []
        for confidence in ("HIGH", "WEAK"):
            inputs.append(
                build_beginner_behavior_contract(
                    ["value = normalize(value)"],
                    [claim()],
                    {"confidence": confidence},
                ).status
            )

        self.assertEqual(inputs[0], inputs[1])

    def test_required_unknown_item_is_always_present(self):
        result = build_beginner_behavior_contract([], [], {})

        self.assertIn(
            "code_outside_observed_range_not_guaranteed",
            result.unknown_items,
        )

    def test_no_runtime_or_performance_claim_is_generated(self):
        result = build_beginner_behavior_contract(
            ["value = normalize(value)"],
            [claim()],
            {},
        )

        statements = " ".join(step.statement for step in result.steps)
        for word in ("success", "performance", "compatible", "side effect"):
            self.assertNotIn(word, statements.lower())

    def test_reference_text_is_not_behavior_evidence(self):
        value = semantic(source="PR")
        result = build_beginner_behavior_contract(
            ["value = normalize(value)"],
            [claim(value)],
            {},
        )

        self.assertIs(result.status, BehaviorStatus.NOT_ESTABLISHED)

    def test_narrative_text_is_not_used(self):
        result = build_beginner_behavior_contract(
            ["value = normalize(value)"],
            [
                {
                    "type": "BEHAVIOR",
                    "safe_statement": "The narrative says it works.",
                    "text": "stdout narrative",
                }
            ],
            {},
        )

        self.assertIs(result.status, BehaviorStatus.NOT_ESTABLISHED)

    def test_empty_current_lines_are_not_established(self):
        result = build_beginner_behavior_contract(
            [],
            [claim()],
            {},
        )

        self.assertIs(result.status, BehaviorStatus.NOT_ESTABLISHED)

    def test_contract_validator_enforces_unknown_item(self):
        from webapp.beginner_behavior import (
            BeginnerBehaviorContract,
        )

        with self.assertRaises(ValueError):
            validate_beginner_behavior_contract(
                BeginnerBehaviorContract(
                    BehaviorStatus.NOT_ESTABLISHED,
                    (),
                    (),
                    (),
                )
            )


if __name__ == "__main__":
    unittest.main()
