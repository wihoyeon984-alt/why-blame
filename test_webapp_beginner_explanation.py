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

    def behavior_contract(
        self,
        status="DIRECTLY_OBSERVED",
        steps=None,
        unknown_items=(
            "code_outside_observed_range_not_guaranteed",
        ),
        limitations=(),
    ):
        return {
            "status": status,
            "steps": steps or [],
            "unknown_items": list(unknown_items),
            "limitation_codes": list(limitations),
        }

    def test_missing_behavior_uses_behavior_fallback(self):
        result = build_easy_explanation_sections(
            evidence_contract(),
            None,
            "en",
        )

        self.assertFalse(result["behavior_available"])
        self.assertIn(
            "structured information",
            result["behavior_fallback"],
        )

    def test_direct_behavior_preserves_statement_and_excerpt(self):
        result = build_easy_explanation_sections(
            None,
            self.behavior_contract(
                steps=[
                    {
                        "statement": "value is used.",
                        "code_excerpt": "value",
                        "is_directly_observed": True,
                        "limitation_codes": [],
                    }
                ]
            ),
            "en",
        )

        self.assertEqual(
            result["behavior_steps"][0]["statement"],
            "value is used.",
        )
        self.assertEqual(
            result["behavior_steps"][0]["code_excerpt"],
            "value",
        )

    def test_partial_behavior_is_not_presented_as_complete(self):
        result = build_easy_explanation_sections(
            None,
            self.behavior_contract(
                status="PARTIALLY_OBSERVED",
                steps=[
                    {
                        "statement": "part is observed.",
                        "code_excerpt": "part",
                        "is_directly_observed": False,
                        "limitation_codes": [
                            "behavior_not_fully_established"
                        ],
                    }
                ]
            ),
            "en",
        )

        self.assertIn("Only part", result["behavior_status"])
        self.assertIn(
            "partly",
            result["behavior_steps"][0]["observation_label"],
        )

    def test_not_established_does_not_render_steps(self):
        result = build_easy_explanation_sections(
            None,
            self.behavior_contract(
                status="NOT_ESTABLISHED",
                steps=[],
            ),
            "en",
        )

        self.assertEqual(result["behavior_steps"], [])
        self.assertIn("could not be established", result["behavior_status"])

    def test_withheld_does_not_render_steps(self):
        result = build_easy_explanation_sections(
            None,
            self.behavior_contract(
                status="WITHHELD",
                steps=[
                    {
                        "statement": "must not render",
                        "code_excerpt": "secret",
                        "is_directly_observed": False,
                        "limitation_codes": [],
                    }
                ],
            ),
            "en",
        )

        self.assertEqual(result["behavior_steps"], [])
        self.assertIn("withheld", result["behavior_status"])

    def test_behavior_unknown_item_is_translated(self):
        result = build_easy_explanation_sections(
            None,
            self.behavior_contract(),
            "ko",
        )

        self.assertIn("선택한 코드 범위 밖", result["behavior_unknown_items"][0])

    def test_unknown_behavior_limitation_uses_fallback(self):
        result = build_easy_explanation_sections(
            None,
            self.behavior_contract(limitations=("new_code",)),
            "en",
        )

        self.assertIn(
            "could not be confirmed",
            result["behavior_limitations"][0],
        )

    def test_behavior_output_excludes_confidence_coverage_and_sha(self):
        result = build_easy_explanation_sections(
            None,
            self.behavior_contract(
                steps=[
                    {
                        "statement": "value is used.",
                        "code_excerpt": "value",
                        "source_event": "abcdef123456",
                        "is_directly_observed": True,
                        "limitation_codes": [],
                    }
                ]
            ),
            "en",
        )

        rendered = repr(result)
        self.assertNotIn("confidence", rendered.lower())
        self.assertNotIn("coverage", rendered.lower())
        self.assertNotIn("abcdef123456", rendered)

    def test_behavior_external_markup_remains_plain_data(self):
        statement = "<b>value</b> **used**"
        result = build_easy_explanation_sections(
            None,
            self.behavior_contract(
                steps=[
                    {
                        "statement": statement,
                        "code_excerpt": "<value>",
                        "is_directly_observed": True,
                        "limitation_codes": [],
                    }
                ]
            ),
            "en",
        )

        self.assertEqual(
            result["behavior_steps"][0]["statement"],
            statement,
        )

    def test_korean_behavior_statement_is_localized(self):
        result = build_easy_explanation_sections(
            None,
            self.behavior_contract(
                steps=[
                    {
                        "statement": "value is used.",
                        "code_excerpt": "value",
                        "is_directly_observed": True,
                        "limitation_codes": [],
                    }
                ]
            ),
            "ko",
        )

        self.assertNotIn(
            "is used",
            result["behavior_steps"][0]["statement"],
        )


    def test_existing_evidence_is_preserved_with_behavior(self):
        result = build_easy_explanation_sections(
            evidence_contract(
                unknown_items=("exact_change_reason_not_recorded",)
            ),
            self.behavior_contract(),
            "en",
        )

        self.assertEqual(len(result["unknown_items"]), 1)
        self.assertTrue(result["behavior_available"])

    def test_target_range_is_displayed(self):
        result = build_easy_explanation_sections(
            evidence_contract(),
            None,
            "ko",
            {
                "file": "service.py",
                "start_line": 4,
                "end_line": 6,
            },
        )

        self.assertEqual(
            result["target_label"],
            "service.py · 4~6번째 줄",
        )

    def test_target_single_line_is_displayed(self):
        result = build_easy_explanation_sections(
            evidence_contract(),
            None,
            "en",
            {
                "file": "service.py",
                "start_line": 4,
                "end_line": 4,
            },
        )

        self.assertEqual(
            result["target_label"],
            "service.py · line 4",
        )

    def test_invalid_target_uses_fallback(self):
        result = build_easy_explanation_sections(
            evidence_contract(),
            None,
            "ko",
            {
                "file": "service.py",
                "start_line": "4",
                "end_line": 6,
            },
        )

        self.assertEqual(
            result["target_label"],
            "분석 대상 정보를 확인할 수 없습니다.",
        )

    def test_not_established_removes_repeated_behavior_limitation(self):
        result = build_easy_explanation_sections(
            None,
            self.behavior_contract(
                status="NOT_ESTABLISHED",
                limitations=("current_behavior_partially_unconfirmed",),
            ),
            "en",
        )

        self.assertEqual(result["behavior_limitations"], [])
        self.assertIn(
            "could not be established",
            result["behavior_status"],
        )

    def test_no_evidence_message_has_no_internal_term(self):
        result = build_easy_explanation_sections(
            evidence_contract(evidence_items=()),
            "en",
        )

        self.assertNotIn(
            "structured",
            result["evidence_question"].lower()
            + repr(result["evidence"]),
        )

    def test_no_limitations_message_is_not_absolute(self):
        result = build_easy_explanation_sections(
            evidence_contract(),
            "ko",
        )

        self.assertIn("기록되지 않은", translate_no_limitations(result))
        self.assertIn("범위 밖", translate_no_limitations(result))


def translate_no_limitations(result):
    from webapp.i18n import translate

    return translate("ko", "easy_no_limitations")


if __name__ == "__main__":
    unittest.main()
