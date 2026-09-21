import unittest

from claim_semantic_mapping import (
    combine_mapping_levels,
    detect_evidence_actions,
    evaluate_action_candidates,
    evaluate_action_mapping,
    evaluate_candidate_action,
)
from claim_semantics import (
    CONFLICTING,
    DIRECT,
    NONE,
    PARTIAL,
)


class TestClaimSemanticMapping(
    unittest.TestCase
):

    def make_candidate(
        self,
        text,
        source_event="abc123",
        matched_tokens=None,
    ):
        return {
            "status": "CANDIDATE",
            "channel": "COMMIT",
            "ref": "abc123",
            "source_event": source_event,
            "matched_tokens": (
                matched_tokens
                or ["context"]
            ),
            "text": text,
        }

    def test_explicit_avoid_action_is_detected(self):
        result = detect_evidence_actions(
            (
                "Don't use the default context "
                "with a custom context"
            )
        )

        self.assertIn(
            "AVOID",
            result,
        )

    def test_explicit_use_entails_use_directly(self):
        result = evaluate_action_mapping(
            "USE",
            "Use the custom context for requests.",
        )

        self.assertEqual(
            result,
            DIRECT,
        )

    def test_explicit_avoid_entails_avoid_directly(self):
        result = evaluate_action_mapping(
            "AVOID",
            (
                "Don't use the default context "
                "when custom configuration exists."
            ),
        )

        self.assertEqual(
            result,
            DIRECT,
        )

    def test_opposite_action_is_conflicting(self):
        result = evaluate_action_mapping(
            "USE",
            (
                "Don't use the custom context "
                "for this path."
            ),
        )

        self.assertEqual(
            result,
            CONFLICTING,
        )

    def test_related_text_without_action_is_partial(self):
        result = evaluate_action_mapping(
            "AVOID",
            (
                "Improve custom context "
                "configuration handling."
            ),
        )

        self.assertEqual(
            result,
            PARTIAL,
        )

    def test_empty_evidence_is_none(self):
        result = evaluate_action_mapping(
            "USE",
            "",
        )

        self.assertEqual(
            result,
            NONE,
        )

    def test_token_overlap_alone_does_not_become_direct(self):
        candidate = self.make_candidate(
            (
                "Improve SSLContext "
                "and poolmanager compatibility"
            ),
            matched_tokens=[
                "ssl",
                "context",
                "poolmanager",
            ],
        )

        result = evaluate_candidate_action(
            "AVOID",
            candidate,
            "abc123",
        )

        self.assertEqual(
            result,
            PARTIAL,
        )

    def test_wrong_source_event_is_none(self):
        candidate = self.make_candidate(
            "Don't use the default context.",
            source_event="old111",
        )

        result = evaluate_candidate_action(
            "AVOID",
            candidate,
            "new222",
        )

        self.assertEqual(
            result,
            NONE,
        )

    def test_missing_matched_tokens_is_none(self):
        candidate = self.make_candidate(
            "Don't use the default context.",
            matched_tokens=[],
        )

        candidate["matched_tokens"] = []

        result = evaluate_candidate_action(
            "AVOID",
            candidate,
            "abc123",
        )

        self.assertEqual(
            result,
            NONE,
        )

    def test_conflicting_candidate_overrides_direct_candidate(self):
        candidates = [
            self.make_candidate(
                "Use the custom context."
            ),
            self.make_candidate(
                "Don't use the custom context."
            ),
        ]

        result = evaluate_action_candidates(
            "USE",
            candidates,
            "abc123",
        )

        self.assertEqual(
            result,
            CONFLICTING,
        )

    def test_multiple_partial_candidates_do_not_become_direct(self):
        candidates = [
            self.make_candidate(
                "Improve custom context support."
            ),
            self.make_candidate(
                "Handle custom context configuration."
            ),
        ]

        result = evaluate_action_candidates(
            "AVOID",
            candidates,
            "abc123",
        )

        self.assertEqual(
            result,
            PARTIAL,
        )

    def test_direct_candidate_remains_direct(self):
        candidates = [
            self.make_candidate(
                "Improve custom context support."
            ),
            self.make_candidate(
                "Don't use the default context."
            ),
        ]

        result = evaluate_action_candidates(
            "AVOID",
            candidates,
            "abc123",
        )

        self.assertEqual(
            result,
            DIRECT,
        )

    def test_empty_candidate_list_is_none(self):
        result = evaluate_action_candidates(
            "USE",
            [],
            "abc123",
        )

        self.assertEqual(
            result,
            NONE,
        )

    def test_direct_plus_partial_stays_direct(self):
        result = combine_mapping_levels(
            [
                PARTIAL,
                DIRECT,
            ]
        )

        self.assertEqual(
            result,
            DIRECT,
        )

    def test_conflicting_always_wins(self):
        result = combine_mapping_levels(
            [
                DIRECT,
                CONFLICTING,
                PARTIAL,
            ]
        )

        self.assertEqual(
            result,
            CONFLICTING,
        )


if __name__ == "__main__":
    unittest.main()