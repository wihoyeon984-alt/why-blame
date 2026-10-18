import unittest
from types import SimpleNamespace

from webapp.beginner_explanation import (
    build_easy_explanation_sections,
)
from webapp.beginner_evidence import (
    EvidenceChannel,
    EvidenceScope,
    EvidenceSupport,
    HistoryCompleteness,
    OriginStatus,
    ReasonStatus,
)


def evidence_contract(
    reason_status=ReasonStatus.NOT_RECORDED,
    evidence_items=(),
    unknown_items=(),
    limitation_codes=(),
    origin_status=OriginStatus.NOT_ESTABLISHED,
):
    return SimpleNamespace(
        reason_status=reason_status,
        evidence_items=evidence_items,
        unknown_items=unknown_items,
        limitation_codes=limitation_codes,
        origin_status=origin_status,
        history_completeness=HistoryCompleteness.UNKNOWN,
    )


def evidence_item(
    channel=EvidenceChannel.PR_TITLE,
    supports=EvidenceSupport.REASON,
    scope=EvidenceScope.HISTORY_ONLY,
    text="plain text",
    truncated=False,
):
    return SimpleNamespace(
        source_channel=channel,
        supports=supports,
        scope=scope,
        text=text,
        is_truncated=truncated,
    )


class BeginnerExplanationTests(unittest.TestCase):
    def test_missing_evidence_uses_fallback(self):
        result = build_easy_explanation_sections(None, "en")

        self.assertFalse(result["available"])
        self.assertIn("structured evidence", result["fallback"])

    def test_reason_statuses_use_fixed_messages(self):
        for status in ReasonStatus:
            with self.subTest(status=status):
                result = build_easy_explanation_sections(
                    evidence_contract(reason_status=status),
                    "en",
                )
                self.assertTrue(result["reason_status"])

    def test_title_only_does_not_claim_a_confirmed_reason(self):
        result = build_easy_explanation_sections(
            evidence_contract(reason_status=ReasonStatus.TITLE_ONLY),
            "en",
        )

        self.assertIn("title", result["reason_status"].lower())
        self.assertNotIn("because", result["reason_status"].lower())

    def test_confidence_and_coverage_are_not_rendered(self):
        result = build_easy_explanation_sections(
            evidence_contract(),
            "en",
        )

        rendered = repr(result)
        self.assertNotIn("confidence", rendered.lower())
        self.assertNotIn("coverage", rendered.lower())

    def test_unknown_items_are_visible(self):
        result = build_easy_explanation_sections(
            evidence_contract(
                unknown_items=("exact_change_reason_not_recorded",)
            ),
            "ko",
        )

        self.assertEqual(len(result["unknown_items"]), 1)
        self.assertIn("확인된 기록", result["unknown_items"][0])

    def test_external_text_is_plain_data(self):
        result = build_easy_explanation_sections(
            evidence_contract(
                evidence_items=(
                    evidence_item(text="<b>not markup</b>"),
                )
            ),
            "en",
        )

        self.assertEqual(
            result["evidence"][0]["text"],
            "<b>not markup</b>",
        )

    def test_origin_does_not_claim_first_creation(self):
        result = build_easy_explanation_sections(
            evidence_contract(
                origin_status=OriginStatus.OBSERVED_IN_HISTORY
            ),
            "en",
        )

        self.assertIn("first appearance", result["origin"])
        self.assertNotIn("created", result["origin"].lower())

    def test_truncated_evidence_has_notice(self):
        result = build_easy_explanation_sections(
            evidence_contract(
                evidence_items=(evidence_item(truncated=True),)
            ),
            "en",
        )

        self.assertTrue(result["evidence"][0]["is_truncated"])
        self.assertIn("partially", result["truncated_notice"])

    def test_history_diff_is_not_direct_behavior(self):
        result = build_easy_explanation_sections(
            evidence_contract(
                evidence_items=(
                    evidence_item(
                        channel=EvidenceChannel.CODE_DIFF,
                        supports=EvidenceSupport.NONE,
                        scope=EvidenceScope.HISTORY_ONLY,
                    ),
                )
            ),
            "en",
        )

        self.assertFalse(result["evidence"][0]["is_direct_behavior"])


if __name__ == "__main__":
    unittest.main()
