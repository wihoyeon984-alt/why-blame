import unittest

from webapp.beginner_evidence import (
    BeginnerEvidenceContract,
    BeginnerEvidenceItem,
    EvidenceChannel,
    EvidenceScope,
    EvidenceSupport,
    HistoryCompleteness,
    OriginStatus,
    ReasonStatus,
    build_beginner_evidence_contract,
    validate_beginner_evidence_contract,
)


def reference(
    ref_type="PR",
    title="A linked change",
    body="Detailed context.",
    truncated=False,
    status="SUCCESS",
):
    return {
        "status": status,
        "type": ref_type,
        "title": title,
        "body_summary": body,
        "body_summary_truncated": truncated,
        "url": "https://example.test/reference/1",
    }


class BeginnerEvidenceTests(unittest.TestCase):
    def test_title_only_is_supported_even_with_high_confidence(self):
        contract = build_beginner_evidence_contract(
            [{"ref_items": [reference(body="")]}],
            {"confidence": "HIGH"},
        )

        self.assertIs(contract.reason_status, ReasonStatus.TITLE_ONLY)

    def test_complete_body_is_independent_of_weak_confidence(self):
        contract = build_beginner_evidence_contract(
            [{"ref_items": [reference()]}],
            {"confidence": "WEAK"},
        )

        self.assertIs(contract.reason_status, ReasonStatus.EXPLICIT_TEXT)

    def test_blocked_reason_is_withheld(self):
        contract = build_beginner_evidence_contract(
            [{"ref_items": [reference()]}],
            {"is_blocked": True},
        )

        self.assertIs(contract.reason_status, ReasonStatus.WITHHELD)

    def test_not_found_reference_is_excluded(self):
        contract = build_beginner_evidence_contract(
            [{"ref_items": [reference(status="NOT_FOUND")]}],
            {},
        )

        self.assertIs(contract.reason_status, ReasonStatus.NOT_RECORDED)
        self.assertEqual(contract.evidence_items, ())

    def test_truncated_body_is_not_explicit_text(self):
        contract = build_beginner_evidence_contract(
            [{"ref_items": [reference(truncated=True)]}],
            {},
        )

        self.assertIs(contract.reason_status, ReasonStatus.TITLE_ONLY)
        self.assertIn(
            "truncated_reference_context",
            contract.unknown_items,
        )

    def test_diff_is_history_only_and_none(self):
        contract = build_beginner_evidence_contract(
            [{"diff_lines": ["+ changed()"]}],
            {},
        )

        item = contract.evidence_items[0]
        self.assertIs(item.scope, EvidenceScope.HISTORY_ONLY)
        self.assertIs(item.supports, EvidenceSupport.NONE)

    def test_unknown_items_invariant(self):
        contract = BeginnerEvidenceContract(
            ReasonStatus.NOT_RECORDED,
            (),
            (),
            (),
            OriginStatus.NOT_ESTABLISHED,
            HistoryCompleteness.UNKNOWN,
        )

        with self.assertRaises(ValueError):
            validate_beginner_evidence_contract(contract)

    def test_duplicate_evidence_id_is_rejected(self):
        item = BeginnerEvidenceItem(
            "duplicate",
            EvidenceChannel.TARGET_CODE,
            EvidenceSupport.BEHAVIOR,
            EvidenceScope.IN_TARGET,
            "code",
            False,
            None,
        )
        contract = BeginnerEvidenceContract(
            ReasonStatus.NOT_RECORDED,
            (item, item),
            ("unrecorded_developer_intent",),
            (),
            OriginStatus.NOT_ESTABLISHED,
            HistoryCompleteness.UNKNOWN,
        )

        with self.assertRaises(ValueError):
            validate_beginner_evidence_contract(contract)

    def test_first_observed_only_sets_origin_status(self):
        contract = build_beginner_evidence_contract(
            [{"type": "FIRST OBSERVED"}],
            {},
        )

        self.assertIs(
            contract.origin_status,
            OriginStatus.OBSERVED_IN_HISTORY,
        )

    def test_contract_has_no_confidence_or_coverage(self):
        contract = build_beginner_evidence_contract([], {})

        self.assertFalse(hasattr(contract, "confidence"))
        self.assertFalse(hasattr(contract, "coverage"))

    def test_inconsistent_consistency_is_withheld(self):
        contract = build_beginner_evidence_contract(
            [{"ref_items": [reference()]}],
            {"consistency": "INCONSISTENT"},
        )

        self.assertIs(contract.reason_status, ReasonStatus.WITHHELD)


if __name__ == "__main__":
    unittest.main()
