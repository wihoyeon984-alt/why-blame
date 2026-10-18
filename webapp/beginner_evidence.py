from dataclasses import dataclass
from enum import Enum


class ReasonStatus(str, Enum):
    EXPLICIT_TEXT = "explicit_text"
    TITLE_ONLY = "title_only"
    NOT_RECORDED = "not_recorded"
    WITHHELD = "withheld"


class EvidenceChannel(str, Enum):
    TARGET_CODE = "target_code"
    CODE_DIFF = "code_diff"
    COMMIT_TITLE = "commit_title"
    PR_TITLE = "pr_title"
    PR_BODY = "pr_body"
    ISSUE_TITLE = "issue_title"
    ISSUE_BODY = "issue_body"


class EvidenceSupport(str, Enum):
    BEHAVIOR = "behavior"
    REASON = "reason"
    NONE = "none"


class EvidenceScope(str, Enum):
    IN_TARGET = "in_target"
    HISTORY_ONLY = "history_only"
    OUT_OF_TARGET = "out_of_target"


class HistoryCompleteness(str, Enum):
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class OriginStatus(str, Enum):
    OBSERVED_IN_HISTORY = "observed_in_history"
    NOT_ESTABLISHED = "not_established"


@dataclass(frozen=True)
class BeginnerEvidenceItem:
    evidence_id: str
    source_channel: EvidenceChannel
    supports: EvidenceSupport
    scope: EvidenceScope
    text: str
    is_truncated: bool
    source_url: str | None


@dataclass(frozen=True)
class BeginnerEvidenceContract:
    reason_status: ReasonStatus
    evidence_items: tuple
    unknown_items: tuple[str, ...]
    limitation_codes: tuple[str, ...]
    origin_status: OriginStatus
    history_completeness: HistoryCompleteness


def _event_references(event):
    references = event.get("ref_items")
    if isinstance(references, (list, tuple)):
        return references
    return ()


def _successful_reference(reference):
    return (
        isinstance(reference, dict)
        and reference.get("status") == "SUCCESS"
        and reference.get("type") in {"PR", "ISSUE"}
    )


def _reference_item(
    event_index,
    reference_index,
    reference,
    channel,
    text,
    is_truncated,
    evidence_id_suffix,
    supports=EvidenceSupport.REASON,
):
    return BeginnerEvidenceItem(
        evidence_id=(
            f"history-{event_index}-reference-{reference_index}-"
            f"{evidence_id_suffix}"
        ),
        source_channel=channel,
        supports=supports,
        scope=EvidenceScope.HISTORY_ONLY,
        text=text,
        is_truncated=is_truncated,
        source_url=reference.get("url") or None,
    )


def _build_evidence_items(timeline):
    evidence_items = []
    has_first_observed = False
    has_external_reference = False
    has_truncated_reference = False

    for event_index, event in enumerate(timeline):
        if not isinstance(event, dict):
            continue

        event_type = event.get("type")
        if (
            isinstance(event_type, str)
            and "FIRST OBSERVED" in event_type.upper()
        ):
            has_first_observed = True

        current_lines = event.get("current_lines")
        if isinstance(current_lines, list):
            for line_index, line in enumerate(current_lines):
                evidence_items.append(
                    BeginnerEvidenceItem(
                        evidence_id=(
                            f"target-{event_index}-current-{line_index}"
                        ),
                        source_channel=EvidenceChannel.TARGET_CODE,
                        supports=EvidenceSupport.BEHAVIOR,
                        scope=EvidenceScope.IN_TARGET,
                        text=str(line),
                        is_truncated=False,
                        source_url=None,
                    )
                )

        diff_lines = event.get("diff_lines")
        if isinstance(diff_lines, list):
            for line_index, line in enumerate(diff_lines):
                evidence_items.append(
                    BeginnerEvidenceItem(
                        evidence_id=f"history-{event_index}-diff-{line_index}",
                        source_channel=EvidenceChannel.CODE_DIFF,
                        supports=EvidenceSupport.NONE,
                        scope=EvidenceScope.HISTORY_ONLY,
                        text=str(line),
                        is_truncated=False,
                        source_url=None,
                    )
                )

        for reference_index, reference in enumerate(
            _event_references(event)
        ):
            if not _successful_reference(reference):
                continue

            ref_type = reference["type"]
            title_channel = (
                EvidenceChannel.PR_TITLE
                if ref_type == "PR"
                else EvidenceChannel.ISSUE_TITLE
            )
            body_channel = (
                EvidenceChannel.PR_BODY
                if ref_type == "PR"
                else EvidenceChannel.ISSUE_BODY
            )
            title = reference.get("title") or ""
            body = reference.get("body_summary") or ""
            body_truncated = (
                reference.get("body_summary_truncated") is True
            )

            if title:
                evidence_items.append(
                    _reference_item(
                        event_index,
                        reference_index,
                        reference,
                        title_channel,
                        title,
                        False,
                        "title",
                    )
                )
                has_external_reference = True

            if body:
                evidence_items.append(
                    _reference_item(
                        event_index,
                        reference_index,
                        reference,
                        body_channel,
                        body,
                        body_truncated,
                        "body",
                        (
                            EvidenceSupport.NONE
                            if body_truncated
                            else EvidenceSupport.REASON
                        ),
                    )
                )
                has_external_reference = True
                has_truncated_reference |= body_truncated

    return (
        tuple(evidence_items),
        has_first_observed,
        has_external_reference,
        has_truncated_reference,
    )


def validate_beginner_evidence_contract(contract):
    if not contract.unknown_items:
        raise ValueError("unknown_items must not be empty.")

    if "unrecorded_developer_intent" not in contract.unknown_items:
        raise ValueError(
            "unknown_items must include unrecorded_developer_intent."
        )

    evidence_items = contract.evidence_items
    if contract.reason_status is ReasonStatus.EXPLICIT_TEXT:
        if not any(
            item.supports is EvidenceSupport.REASON
            and not item.is_truncated
            for item in evidence_items
        ):
            raise ValueError(
                "EXPLICIT_TEXT requires untruncated reason evidence."
            )

    if contract.reason_status is ReasonStatus.TITLE_ONLY:
        if any(
            item.supports is EvidenceSupport.REASON
            and item.source_channel
            in {
                EvidenceChannel.PR_BODY,
                EvidenceChannel.ISSUE_BODY,
            }
            for item in evidence_items
        ):
            raise ValueError(
                "TITLE_ONLY cannot use PR or ISSUE body evidence."
            )

    seen_ids = set()
    for item in evidence_items:
        if not item.evidence_id:
            raise ValueError("evidence_id must not be empty.")
        if item.evidence_id in seen_ids:
            raise ValueError("evidence_id values must be unique.")
        seen_ids.add(item.evidence_id)

        if (
            item.source_channel is EvidenceChannel.CODE_DIFF
            and item.scope
            in {
                EvidenceScope.OUT_OF_TARGET,
                EvidenceScope.HISTORY_ONLY,
            }
            and item.supports is EvidenceSupport.BEHAVIOR
        ):
            raise ValueError(
                "Out-of-target or history-only diffs cannot support behavior."
            )

    return contract


def build_beginner_evidence_contract(timeline, stats):
    timeline = timeline if isinstance(timeline, list) else []
    stats = stats if isinstance(stats, dict) else {}
    (
        evidence_items,
        has_first_observed,
        has_external_reference,
        has_truncated_reference,
    ) = _build_evidence_items(timeline)

    valid_body = any(
        item.supports is EvidenceSupport.REASON
        and item.source_channel
        in {
            EvidenceChannel.PR_BODY,
            EvidenceChannel.ISSUE_BODY,
        }
        and item.text
        and not item.is_truncated
        for item in evidence_items
    )
    has_title = any(
        item.supports is EvidenceSupport.REASON
        and item.source_channel
        in {
            EvidenceChannel.PR_TITLE,
            EvidenceChannel.ISSUE_TITLE,
        }
        and item.text
        for item in evidence_items
    )

    if stats.get("is_blocked") is True or (
        stats.get("consistency") == "INCONSISTENT"
    ):
        reason_status = ReasonStatus.WITHHELD
    elif valid_body:
        reason_status = ReasonStatus.EXPLICIT_TEXT
    elif has_title:
        reason_status = ReasonStatus.TITLE_ONLY
    else:
        reason_status = ReasonStatus.NOT_RECORDED

    unknown_items = ["unrecorded_developer_intent"]
    if not has_external_reference:
        unknown_items.append("exact_change_reason_not_recorded")
    if has_truncated_reference:
        unknown_items.append("truncated_reference_context")

    limitations = stats.get("limitations", ())
    if not isinstance(limitations, (list, tuple)):
        limitations = ()

    history_completeness = HistoryCompleteness.UNKNOWN
    if stats.get("history_completeness") == HistoryCompleteness.PARTIAL.value:
        history_completeness = HistoryCompleteness.PARTIAL

    contract = BeginnerEvidenceContract(
        reason_status=reason_status,
        evidence_items=evidence_items,
        unknown_items=tuple(unknown_items),
        limitation_codes=tuple(str(item) for item in limitations),
        origin_status=(
            OriginStatus.OBSERVED_IN_HISTORY
            if has_first_observed
            else OriginStatus.NOT_ESTABLISHED
        ),
        history_completeness=history_completeness,
    )
    return validate_beginner_evidence_contract(contract)
