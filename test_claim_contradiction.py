import unittest

from claim_contradiction import (
    NO_CONTRADICTION,
    actions_contradict,
    collect_contradictions,
    contradiction_free,
    evaluate_contradiction,
)
from claim_semantics import (
    CONFLICTING,
    make_behavior_semantics,
)


class TestClaimContradiction(unittest.TestCase):

    def test_use_and_avoid_are_opposites(self):
        self.assertTrue(
            actions_contradict(
                "USE",
                "AVOID",
            )
        )

        self.assertTrue(
            actions_contradict(
                "AVOID",
                "USE",
            )
        )

    def test_enable_and_disable_are_opposites(self):
        self.assertTrue(
            actions_contradict(
                "ENABLE",
                "DISABLE",
            )
        )

    def test_same_action_is_not_contradiction(self):
        self.assertFalse(
            actions_contradict(
                "USE",
                "USE",
            )
        )

    def test_unrelated_actions_are_not_assumed_to_conflict(self):
        self.assertFalse(
            actions_contradict(
                "ENCODE",
                "VALIDATE",
            )
        )

    def test_same_target_with_opposite_action_conflicts(self):
        claim = make_behavior_semantics(
            action="USE",
            subject="custom context",
            target="poolmanager",
            source_event="abc123",
        )

        evidence = make_behavior_semantics(
            action="AVOID",
            subject="custom context",
            target="poolmanager",
            source_event="abc123",
        )

        result = evaluate_contradiction(
            claim,
            evidence,
        )

        self.assertEqual(
            result,
            CONFLICTING,
        )

    def test_different_target_does_not_conflict(self):
        claim = make_behavior_semantics(
            action="USE",
            subject="custom context",
            target="poolmanager",
            source_event="abc123",
        )

        evidence = make_behavior_semantics(
            action="AVOID",
            subject="custom context",
            target="renderer",
            source_event="abc123",
        )

        result = evaluate_contradiction(
            claim,
            evidence,
        )

        self.assertEqual(
            result,
            NO_CONTRADICTION,
        )

    def test_token_similarity_does_not_create_contradiction(self):
        claim = make_behavior_semantics(
            action="USE",
            subject="cache",
            target="request path",
            source_event="abc123",
        )

        evidence = make_behavior_semantics(
            action="MEASURE",
            subject="cache",
            target="request path",
            source_event="abc123",
        )

        result = evaluate_contradiction(
            claim,
            evidence,
        )

        self.assertEqual(
            result,
            NO_CONTRADICTION,
        )

    def test_collects_only_explicit_contradictions(self):
        claim = make_behavior_semantics(
            action="ENABLE",
            subject="feature flag",
            target="command",
            source_event="abc123",
        )

        evidence_items = [
            {
                "source": "COMMIT",
                "ref": "abc123",
                "semantics": (
                    make_behavior_semantics(
                        action="ENABLE",
                        subject="feature flag",
                        target="command",
                        source_event="abc123",
                    )
                ),
            },
            {
                "source": "PR",
                "ref": "#10",
                "semantics": (
                    make_behavior_semantics(
                        action="DISABLE",
                        subject="feature flag",
                        target="command",
                        source_event="abc123",
                    )
                ),
            },
        ]

        result = collect_contradictions(
            claim,
            evidence_items,
        )

        self.assertEqual(
            len(result),
            1,
        )

        self.assertEqual(
            result[0]["source"],
            "PR",
        )

        self.assertEqual(
            result[0]["status"],
            CONFLICTING,
        )

    def test_contradiction_free_does_not_mean_entailment(self):
        claim = make_behavior_semantics(
            action="ENCODE",
            subject="string input",
            target="UTF-8",
            source_event="abc123",
        )

        evidence_items = [
            {
                "source": "PR",
                "ref": "#10",
                "semantics": (
                    make_behavior_semantics(
                        action="VALIDATE",
                        subject="string input",
                        target="UTF-8",
                        source_event="abc123",
                    )
                ),
            }
        ]

        self.assertTrue(
            contradiction_free(
                claim,
                evidence_items,
            )
        )


if __name__ == "__main__":
    unittest.main()
