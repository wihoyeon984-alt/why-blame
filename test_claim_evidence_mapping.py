import unittest

from claim_evidence_mapping import (
    CANDIDATE,
    CHANNEL_COMMIT,
    CHANNEL_PR,
    collect_event_evidence,
    map_delta_to_event_evidence,
    map_predicate_to_evidence,
)
from claim_predicate import (
    PREDICATE_NAME,
    PREDICATE_NOT,
)
from claim_predicate_diff import (
    predicate_delta_from_code,
)


class TestClaimEvidenceMapping(unittest.TestCase):

    def test_commit_message_is_collected_as_event_evidence(self):
        event = {
            "hash": "abc123",
            "message": "Preserve custom context",
            "ref_items": [],
        }

        result = collect_event_evidence(
            event
        )

        self.assertEqual(
            len(result),
            1,
        )

        self.assertEqual(
            result[0]["channel"],
            CHANNEL_COMMIT,
        )

        self.assertEqual(
            result[0]["source_event"],
            "abc123",
        )

    def test_successful_pr_is_collected(self):
        event = {
            "hash": "abc123",
            "message": "",
            "ref_items": [
                {
                    "status": "SUCCESS",
                    "type": "PR",
                    "number": 10,
                    "title": (
                        "Preserve custom SSLContext"
                    ),
                    "body": (
                        "Support custom poolmanager context."
                    ),
                }
            ],
        }

        result = collect_event_evidence(
            event
        )

        self.assertEqual(
            len(result),
            1,
        )

        self.assertEqual(
            result[0]["channel"],
            CHANNEL_PR,
        )

        self.assertEqual(
            result[0]["ref"],
            "#10",
        )

    def test_not_found_reference_is_not_evidence_candidate(self):
        event = {
            "hash": "abc123",
            "message": "",
            "ref_items": [
                {
                    "status": "NOT_FOUND",
                    "type": "PR",
                    "number": 10,
                    "title": (
                        "Preserve custom SSLContext"
                    ),
                    "body": "",
                }
            ],
        }

        result = collect_event_evidence(
            event
        )

        self.assertEqual(
            result,
            [],
        )

    def test_identifier_overlap_creates_candidate(self):
        predicate = {
            "op": PREDICATE_NOT,
            "operand": {
                "op": PREDICATE_NAME,
                "name": (
                    "has_poolmanager_ssl_context"
                ),
            },
        }

        evidence = {
            "channel": CHANNEL_COMMIT,
            "ref": "abc123",
            "source_event": "abc123",
            "text": (
                "Don't use default SSLContext "
                "with custom poolmanager kwargs"
            ),
        }

        result = map_predicate_to_evidence(
            predicate,
            evidence,
        )

        self.assertIsNotNone(
            result
        )

        self.assertEqual(
            result["status"],
            CANDIDATE,
        )

        self.assertIn(
            "poolmanager",
            result["matched_tokens"],
        )

        self.assertIn(
            "context",
            result["matched_tokens"],
        )

    def test_unrelated_evidence_does_not_create_candidate(self):
        predicate = {
            "op": PREDICATE_NAME,
            "name": "payment_validation",
        }

        evidence = {
            "channel": CHANNEL_PR,
            "ref": "#10",
            "source_event": "abc123",
            "text": "Improve image rendering",
        }

        result = map_predicate_to_evidence(
            predicate,
            evidence,
        )

        self.assertIsNone(
            result
        )

    def test_candidate_does_not_claim_entailment_level(self):
        predicate = {
            "op": PREDICATE_NAME,
            "name": "cache_enabled",
        }

        evidence = {
            "channel": CHANNEL_COMMIT,
            "ref": "abc123",
            "source_event": "abc123",
            "text": "Disable cache behavior",
        }

        result = map_predicate_to_evidence(
            predicate,
            evidence,
        )

        self.assertIsNotNone(
            result
        )

        self.assertNotIn(
            "entailment",
            result,
        )

        self.assertNotIn(
            "level",
            result,
        )

    def test_delta_maps_only_same_event_evidence(self):
        delta = predicate_delta_from_code(
            "elif verify is True:",
            (
                "elif verify is True and not "
                "has_poolmanager_ssl_context:"
            ),
        )

        event = {
            "hash": "final123",
            "message": (
                "Don't use default SSLContext "
                "with custom poolmanager kwargs"
            ),
            "ref_items": [],
        }

        result = map_delta_to_event_evidence(
            delta,
            event,
        )

        self.assertGreaterEqual(
            len(result["added"]),
            1,
        )

        self.assertEqual(
            result["removed"],
            [],
        )

        self.assertTrue(
            all(
                item["source_event"]
                == "final123"
                for item in result["added"]
            )
        )

    def test_preserved_predicate_is_not_mapped(self):
        delta = predicate_delta_from_code(
            "elif verify is True:",
            (
                "elif verify is True and not "
                "has_poolmanager_ssl_context:"
            ),
        )

        event = {
            "hash": "final123",
            "message": (
                "Verify custom poolmanager SSLContext"
            ),
            "ref_items": [],
        }

        result = map_delta_to_event_evidence(
            delta,
            event,
        )

        for item in result["added"]:
            self.assertNotIn(
                "verify",
                item["matched_tokens"],
            )

    def test_mapping_does_not_generate_semantic_claim(self):
        delta = predicate_delta_from_code(
            "elif verify is True:",
            (
                "elif verify is True and not "
                "has_poolmanager_ssl_context:"
            ),
        )

        event = {
            "hash": "final123",
            "message": (
                "Don't use default SSLContext "
                "with custom poolmanager kwargs"
            ),
            "ref_items": [],
        }

        result = map_delta_to_event_evidence(
            delta,
            event,
        )

        text = repr(
            result
        )

        self.assertNotIn(
            "SAFE_TO_RENDER",
            text,
        )

        self.assertNotIn(
            "DIRECT",
            text,
        )

        self.assertNotIn(
            "custom SSLContext exists",
            text,
        )


if __name__ == "__main__":
    unittest.main()