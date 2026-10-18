from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BehaviorStatus(str, Enum):
    DIRECTLY_OBSERVED = "DIRECTLY_OBSERVED"
    PARTIALLY_OBSERVED = "PARTIALLY_OBSERVED"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"
    WITHHELD = "WITHHELD"


@dataclass(frozen=True)
class BeginnerBehaviorStep:
    step_id: str
    statement: str
    code_excerpt: str
    source_event: str | None
    is_directly_observed: bool
    limitation_codes: tuple[str, ...]


@dataclass(frozen=True)
class BeginnerBehaviorContract:
    status: BehaviorStatus
    steps: tuple[BeginnerBehaviorStep, ...]
    unknown_items: tuple[str, ...]
    limitation_codes: tuple[str, ...]


_UNKNOWN_CODE = "code_outside_observed_range_not_guaranteed"
_DIRECT = "DIRECT"
_PARTIAL = "PARTIAL"
_CONFLICTING = "CONFLICTING"
_SAFE = "SAFE_TO_RENDER"
_BLOCK = "BLOCK"


def _current_text(current_lines):
    if not isinstance(current_lines, (list, tuple)):
        return ""
    if not all(isinstance(line, str) for line in current_lines):
        return ""
    return "\n".join(current_lines)


def _semantic_fields(semantic):
    return {
        field
        for field in (
            "action",
            "subject",
            "condition",
            "target",
            "scope",
        )
        if semantic.get(field) not in (None, "")
    }


def _field_levels(semantic):
    field_evidence = semantic.get("field_evidence", {})
    if not isinstance(field_evidence, dict):
        return {}

    return {
        field: {
            evidence.get("level")
            for evidence in evidence_items
            if isinstance(evidence, dict)
        }
        for field, evidence_items in field_evidence.items()
        if isinstance(evidence_items, (list, tuple))
    }


def _has_conflicting_evidence(semantic):
    return any(
        _CONFLICTING in levels
        for levels in _field_levels(semantic).values()
    )


def _all_fields_direct(semantic, current_text):
    fields = _semantic_fields(semantic)
    levels = _field_levels(semantic)
    semantic_excerpt = any(
        isinstance(semantic.get(key), str)
        and semantic.get(key)
        and semantic.get(key) in current_text
        for key in ("code_excerpt", "source_text")
    )
    return bool(fields) and all(
        _DIRECT in levels.get(field, set())
        and _CONFLICTING not in levels.get(field, set())
        and (
            semantic_excerpt
            or any(
                evidence.get("level") == _DIRECT
                and any(
                    isinstance(evidence.get(key), str)
                    and evidence.get(key)
                    and evidence.get(key) in current_text
                    for key in ("code_excerpt", "source_text")
                )
                for evidence in semantic.get(
                    "field_evidence",
                    {},
                ).get(field, ())
                if isinstance(evidence, dict)
            )
        )
        for field in fields
    )


def _has_partial_fields(semantic):
    fields = _semantic_fields(semantic)
    levels = _field_levels(semantic)
    return bool(fields) and any(
        _PARTIAL in levels.get(field, set())
        or _DIRECT not in levels.get(field, set())
        for field in fields
    )


def _evidence_values(semantic):
    values = []
    for evidence_items in _field_levels_with_items(semantic):
        for evidence in evidence_items:
            if not isinstance(evidence, dict):
                continue
            for key in ("code_excerpt", "source_text"):
                value = evidence.get(key)
                if isinstance(value, str) and value:
                    values.append(value)

    for key in ("code_excerpt", "source_text"):
        value = semantic.get(key)
        if isinstance(value, str) and value:
            values.append(value)

    return tuple(dict.fromkeys(values))


def _field_levels_with_items(semantic):
    field_evidence = semantic.get("field_evidence", {})
    if not isinstance(field_evidence, dict):
        return ()
    return (
        evidence_items
        for evidence_items in field_evidence.values()
        if isinstance(evidence_items, (list, tuple))
    )


def _has_external_behavior_evidence(semantic):
    for evidence_items in _field_levels_with_items(semantic):
        for evidence in evidence_items:
            if not isinstance(evidence, dict):
                continue
            if evidence.get("source") in {"PR", "ISSUE"}:
                return True
    return False


def _safe_statement(claim, semantic):
    for item in (semantic, claim):
        statement = item.get("safe_statement")
        if isinstance(statement, str) and statement.strip():
            return statement.strip()
    return ""


def _source_event(claim, semantic):
    source_event = semantic.get("source_event") or claim.get("source_event")
    return source_event if isinstance(source_event, str) else None


def _make_step(claim, semantic, current_text, index):
    statement = _safe_statement(claim, semantic)
    excerpts = _evidence_values(semantic)
    matching_excerpt = next(
        (excerpt for excerpt in excerpts if excerpt in current_text),
        "",
    )
    has_exact_excerpt = bool(matching_excerpt)
    all_direct = _all_fields_direct(semantic, current_text)
    partial_fields = _has_partial_fields(semantic)
    external_evidence = _has_external_behavior_evidence(semantic)

    if (
        not statement
        or not has_exact_excerpt
        or external_evidence
    ):
        return None, False, False

    directly_observed = (
        claim.get("type") == "BEHAVIOR"
        and claim.get("target_relevant") is True
        and (
            claim.get("semantic_safety") == _SAFE
            or semantic.get("semantic_safety") == _SAFE
        )
        and all_direct
    )

    limitation_codes = ()
    if partial_fields or not directly_observed:
        limitation_codes = ("behavior_fields_partially_observed",)

    step = BeginnerBehaviorStep(
        step_id=f"behavior-{index}",
        statement=statement,
        code_excerpt=matching_excerpt,
        source_event=_source_event(claim, semantic),
        is_directly_observed=directly_observed,
        limitation_codes=limitation_codes,
    )
    return step, directly_observed, True


def validate_beginner_behavior_contract(contract):
    if not contract.unknown_items:
        raise ValueError("unknown_items must not be empty.")
    if _UNKNOWN_CODE not in contract.unknown_items:
        raise ValueError(
            "unknown_items must include code_outside_observed_range_not_guaranteed."
        )

    for step in contract.steps:
        if not step.statement:
            raise ValueError("behavior step statements must not be empty.")
        if (
            contract.status is BehaviorStatus.DIRECTLY_OBSERVED
            and not step.is_directly_observed
        ):
            raise ValueError(
                "DIRECTLY_OBSERVED steps must be directly observed."
            )
        if (
            contract.status is BehaviorStatus.DIRECTLY_OBSERVED
            and not step.code_excerpt
        ):
            raise ValueError(
                "DIRECTLY_OBSERVED steps need a code excerpt."
            )

    if (
        contract.status is BehaviorStatus.DIRECTLY_OBSERVED
        and not contract.steps
    ):
        raise ValueError(
            "DIRECTLY_OBSERVED requires at least one step."
        )

    if (
        contract.status is BehaviorStatus.WITHHELD
        and contract.steps
    ):
        raise ValueError("WITHHELD cannot contain behavior steps.")

    return contract


def build_beginner_behavior_contract(
    current_lines,
    structured_claims,
    stats,
):
    current_text = _current_text(current_lines)
    claims = (
        structured_claims
        if isinstance(structured_claims, (list, tuple))
        else ()
    )
    stats = stats if isinstance(stats, dict) else {}

    withheld = (
        stats.get("is_blocked") is True
        or stats.get("consistency") == "INCONSISTENT"
        or any(
            claim.get("semantic_safety") == _BLOCK
            for claim in claims
            if isinstance(claim, dict)
        )
        or any(
            semantic.get("semantic_safety") == _BLOCK
            for claim in claims
            if isinstance(claim, dict)
            for semantic in claim.get("structured_semantics", ())
            if isinstance(semantic, dict)
        )
        or any(
            _has_conflicting_evidence(semantic)
            for claim in claims
            if isinstance(claim, dict)
            for semantic in claim.get("structured_semantics", ())
            if isinstance(semantic, dict)
        )
    )

    unknown_items = (_UNKNOWN_CODE,)
    if withheld:
        return validate_beginner_behavior_contract(
            BeginnerBehaviorContract(
                status=BehaviorStatus.WITHHELD,
                steps=(),
                unknown_items=unknown_items,
                limitation_codes=("behavior_evidence_withheld",),
            )
        )

    steps = []
    direct_count = 0
    partial_count = 0
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        for semantic in claim.get("structured_semantics", ()):
            if not isinstance(semantic, dict):
                continue
            if (
                claim.get("type") != "BEHAVIOR"
                or claim.get("target_relevant") is not True
            ):
                continue
            step, directly_observed, usable = _make_step(
                claim,
                semantic,
                current_text,
                len(steps),
            )
            if not usable:
                continue
            steps.append(step)
            if directly_observed:
                direct_count += 1
            else:
                partial_count += 1

    if direct_count and partial_count == 0:
        status = BehaviorStatus.DIRECTLY_OBSERVED
        limitation_codes = ()
    elif partial_count:
        status = BehaviorStatus.PARTIALLY_OBSERVED
        limitation_codes = ("behavior_not_fully_established",)
    else:
        status = BehaviorStatus.NOT_ESTABLISHED
        limitation_codes = ("behavior_not_established",)
        steps = ()

    return validate_beginner_behavior_contract(
        BeginnerBehaviorContract(
            status=status,
            steps=tuple(steps),
            unknown_items=unknown_items,
            limitation_codes=limitation_codes,
        )
    )
