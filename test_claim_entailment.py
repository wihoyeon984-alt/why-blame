import unittest

from claim_entailment import (
    evaluate_field_entailment,
    evaluate_semantic_entailment,
    is_safe_for_semantic_rendering,
    with_entailment,
)
from claim_semantics import (
    CONFLICTING,
    DIRECT,
    INFERRED,
    NONE,
    PARTIAL,
    attach_field_evidence,
    make_behavior_semantics,
)


class TestClaimEntailment(unittest.TestCase):

    def test_direct_field_evidence_is_direct(self):
        semantics = make_behavior_semantics(
            action="ENCODE",
            source_event="abc123",
        )

        semantics = attach_field_evidence(
            semantics,
            "action",
            source="DIFF",
            ref="abc123",
            level=DIRECT,
        )

        result = evaluate_field_entailment(
            semantics,
            "action",
        )

        self.assertEqual(
            result,
            DIRECT,
        )

    def test_missing_field_evidence_is_none(self):
        semantics = make_behavior_semantics(
            action="ENCODE",
            source_event="abc123",
        )

        result = evaluate_field_entailment(
            semantics,
            "action",
        )

        self.assertEqual(
            result,
            NONE,
        )

    def test_conflicting_field_evidence_wins(self):
        semantics = make_behavior_semantics(
            action="ENCODE",
            source_event="abc123",
        )

        semantics = attach_field_evidence(
            semantics,
            "action",
            source="DIFF",
            ref="abc123",
            level=DIRECT,
        )

        semantics = attach_field_evidence(
            semantics,
            "action",
            source="PR",
            ref="#10",
            level=CONFLICTING,
        )

        result = evaluate_field_entailment(
            semantics,
            "action",
        )

        self.assertEqual(
            result,
            CONFLICTING,
        )

    def test_all_direct_fields_make_direct_claim(self):
        semantics = make_behavior_semantics(
            action="ENCODE",
            subject="string input",
            target="UTF-8",
            source_event="abc123",
        )

        for field in (
            "action",
            "subject",
            "target",
        ):
            semantics = attach_field_evidence(
                semantics,
                field,
                source="DIFF",
                ref="abc123",
                level=DIRECT,
            )

        result = evaluate_semantic_entailment(
            semantics
        )

        self.assertEqual(
            result,
            DIRECT,
        )

        self.assertTrue(
            is_safe_for_semantic_rendering(
                semantics
            )
        )

    def test_missing_field_makes_claim_none(self):
        semantics = make_behavior_semantics(
            action="ENCODE",
            subject="string input",
            target="UTF-8",
            source_event="abc123",
        )

        semantics = attach_field_evidence(
            semantics,
            "action",
            source="DIFF",
            ref="abc123",
            level=DIRECT,
        )

        semantics = attach_field_evidence(
            semantics,
            "target",
            source="DIFF",
            ref="abc123",
            level=DIRECT,
        )

        result = evaluate_semantic_entailment(
            semantics
        )

        self.assertEqual(
            result,
            NONE,
        )

        self.assertFalse(
            is_safe_for_semantic_rendering(
                semantics
            )
        )

    def test_partial_field_makes_claim_partial(self):
        semantics = make_behavior_semantics(
            action="AVOID",
            subject="default context",
            source_event="abc123",
        )

        semantics = attach_field_evidence(
            semantics,
            "action",
            source="DIFF",
            ref="abc123",
            level=DIRECT,
        )

        semantics = attach_field_evidence(
            semantics,
            "subject",
            source="COMMIT",
            ref="abc123",
            level=PARTIAL,
        )

        result = evaluate_semantic_entailment(
            semantics
        )

        self.assertEqual(
            result,
            PARTIAL,
        )

        self.assertFalse(
            is_safe_for_semantic_rendering(
                semantics
            )
        )

    def test_inferred_field_blocks_direct_rendering(self):
        semantics = make_behavior_semantics(
            action="AVOID",
            condition="custom context exists",
            source_event="abc123",
        )

        semantics = attach_field_evidence(
            semantics,
            "action",
            source="DIFF",
            ref="abc123",
            level=DIRECT,
        )

        semantics = attach_field_evidence(
            semantics,
            "condition",
            source="PR",
            ref="#10",
            level=INFERRED,
        )

        result = evaluate_semantic_entailment(
            semantics
        )

        self.assertEqual(
            result,
            INFERRED,
        )

        self.assertFalse(
            is_safe_for_semantic_rendering(
                semantics
            )
        )

    def test_any_conflicting_field_blocks_whole_claim(self):
        semantics = make_behavior_semantics(
            action="USE",
            subject="custom context",
            source_event="abc123",
        )

        semantics = attach_field_evidence(
            semantics,
            "action",
            source="DIFF",
            ref="abc123",
            level=DIRECT,
        )

        semantics = attach_field_evidence(
            semantics,
            "subject",
            source="PR",
            ref="#10",
            level=CONFLICTING,
        )

        result = evaluate_semantic_entailment(
            semantics
        )

        self.assertEqual(
            result,
            CONFLICTING,
        )

        self.assertFalse(
            is_safe_for_semantic_rendering(
                semantics
            )
        )

    def test_with_entailment_does_not_mutate_original(self):
        semantics = make_behavior_semantics(
            action="ENCODE",
            subject="string input",
            source_event="abc123",
        )

        for field in (
            "action",
            "subject",
        ):
            semantics = attach_field_evidence(
                semantics,
                field,
                source="DIFF",
                ref="abc123",
                level=DIRECT,
            )

        evaluated = with_entailment(
            semantics
        )

        self.assertEqual(
            semantics["entailment"],
            NONE,
        )

        self.assertNotIn(
            "field_entailment",
            semantics,
        )

        self.assertEqual(
            evaluated["entailment"],
            DIRECT,
        )

        self.assertEqual(
            evaluated["field_entailment"],
            {
                "action": DIRECT,
                "subject": DIRECT,
            },
        )


if __name__ == "__main__":
    unittest.main()
