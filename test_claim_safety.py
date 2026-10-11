import unittest

from claim_safety import (
    BLOCK,
    SAFE_TO_RENDER,
    collect_safe_semantics,
    evaluate_semantic_safety,
    with_semantic_safety,
)
from claim_semantics import (
    CONFLICTING,
    DIRECT,
    INFERRED,
    PARTIAL,
    attach_field_evidence,
    make_behavior_semantics,
)


class TestClaimSafety(unittest.TestCase):

    def make_direct_semantics(
        self,
        action="USE",
        subject="custom context",
        target="poolmanager",
    ):
        semantics = make_behavior_semantics(
            action=action,
            subject=subject,
            target=target,
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

        return semantics

    def test_direct_without_contradiction_is_safe(self):
        semantics = self.make_direct_semantics()

        result = evaluate_semantic_safety(
            semantics,
            [],
        )

        self.assertEqual(
            result,
            SAFE_TO_RENDER,
        )

    def test_partial_entailment_is_blocked(self):
        semantics = self.make_direct_semantics()

        semantics = attach_field_evidence(
            semantics,
            "subject",
            source="PR",
            ref="#10",
            level=PARTIAL,
        )

        direct_subject_evidence = (
            semantics["field_evidence"]["subject"]
        )

        direct_subject_evidence[:] = [
            item
            for item in direct_subject_evidence
            if item["level"] != DIRECT
        ]

        result = evaluate_semantic_safety(
            semantics,
            [],
        )

        self.assertEqual(
            result,
            BLOCK,
        )

    def test_inferred_entailment_is_blocked(self):
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
            level=INFERRED,
        )

        result = evaluate_semantic_safety(
            semantics,
            [],
        )

        self.assertEqual(
            result,
            BLOCK,
        )

    def test_missing_evidence_is_blocked(self):
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

        result = evaluate_semantic_safety(
            semantics,
            [],
        )

        self.assertEqual(
            result,
            BLOCK,
        )

    def test_direct_claim_with_contradiction_is_blocked(self):
        semantics = self.make_direct_semantics(
            action="USE"
        )

        conflicting = make_behavior_semantics(
            action="AVOID",
            subject="custom context",
            target="poolmanager",
            source_event="abc123",
        )

        evidence_items = [
            {
                "source": "PR",
                "ref": "#10",
                "semantics": conflicting,
            }
        ]

        result = evaluate_semantic_safety(
            semantics,
            evidence_items,
        )

        self.assertEqual(
            result,
            BLOCK,
        )

    def test_no_contradiction_does_not_rescue_none_entailment(self):
        semantics = make_behavior_semantics(
            action="ENCODE",
            subject="string input",
            target="UTF-8",
            source_event="abc123",
        )

        result = evaluate_semantic_safety(
            semantics,
            [],
        )

        self.assertEqual(
            result,
            BLOCK,
        )

    def test_unrelated_evidence_does_not_block_direct_claim(self):
        semantics = self.make_direct_semantics(
            action="USE"
        )

        unrelated = make_behavior_semantics(
            action="MEASURE",
            subject="custom context",
            target="poolmanager",
            source_event="abc123",
        )

        evidence_items = [
            {
                "source": "PR",
                "ref": "#10",
                "semantics": unrelated,
            }
        ]

        result = evaluate_semantic_safety(
            semantics,
            evidence_items,
        )

        self.assertEqual(
            result,
            SAFE_TO_RENDER,
        )

    def test_with_semantic_safety_preserves_original(self):
        semantics = self.make_direct_semantics()

        evaluated = with_semantic_safety(
            semantics,
            [],
        )

        self.assertNotIn(
            "semantic_safety",
            semantics,
        )

        self.assertEqual(
            evaluated["entailment"],
            DIRECT,
        )

        self.assertEqual(
            evaluated["semantic_safety"],
            SAFE_TO_RENDER,
        )

    def test_collect_safe_semantics_filters_blocked_claims(self):
        safe = self.make_direct_semantics(
            action="USE"
        )

        blocked = make_behavior_semantics(
            action="AVOID",
            subject="default context",
            source_event="abc123",
        )

        blocked = attach_field_evidence(
            blocked,
            "action",
            source="DIFF",
            ref="abc123",
            level=DIRECT,
        )

        items = [
            {
                "semantics": safe,
                "evidence_items": [],
            },
            {
                "semantics": blocked,
                "evidence_items": [],
            },
        ]

        result = collect_safe_semantics(
            items
        )

        self.assertEqual(
            len(result),
            1,
        )

        self.assertEqual(
            result[0]["action"],
            "USE",
        )

        self.assertEqual(
            result[0]["semantic_safety"],
            SAFE_TO_RENDER,
        )


if __name__ == "__main__":
    unittest.main()