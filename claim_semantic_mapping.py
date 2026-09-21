import re

from claim_semantics import (
    CONFLICTING,
    DIRECT,
    NONE,
    PARTIAL,
)


_ACTION_PATTERNS = {
    "USE": (
        r"\buse\b",
        r"\buses\b",
        r"\busing\b",
    ),
    "AVOID": (
        r"\bavoid\b",
        r"\bavoids\b",
        r"\bdo not use\b",
        r"\bdon't use\b",
        r"\bnot use\b",
    ),
    "ENABLE": (
        r"\benable\b",
        r"\benables\b",
        r"\benabled\b",
    ),
    "DISABLE": (
        r"\bdisable\b",
        r"\bdisables\b",
        r"\bdisabled\b",
    ),
    "ADD": (
        r"\badd\b",
        r"\badds\b",
        r"\badded\b",
    ),
    "REMOVE": (
        r"\bremove\b",
        r"\bremoves\b",
        r"\bremoved\b",
    ),
}


_ACTION_OPPOSITES = {
    "USE": "AVOID",
    "AVOID": "USE",
    "ENABLE": "DISABLE",
    "DISABLE": "ENABLE",
    "ADD": "REMOVE",
    "REMOVE": "ADD",
}


def detect_evidence_actions(text):
    """
    Evidence text에서 명시적으로 표현된 action 후보를 찾습니다.

    부정 action 표현을 positive action보다 먼저 처리합니다.

    예:
        "Don't use default context"
        -> AVOID

    위 문장을 AVOID와 USE를 동시에 의미한다고 처리하지 않습니다.

    등록된 명시적 표현만 인식하며,
    자유로운 의미 추론은 수행하지 않습니다.
    """
    if not isinstance(text, str):
        return set()

    lowered = text.lower()

    result = set()

    avoid_patterns = (
        r"\bavoid\b",
        r"\bavoids\b",
        r"\bdo not use\b",
        r"\bdon't use\b",
        r"\bnot use\b",
    )

    avoid_detected = any(
        re.search(pattern, lowered)
        for pattern in avoid_patterns
    )

    if avoid_detected:
        result.add("AVOID")

    for action, patterns in _ACTION_PATTERNS.items():
        if action == "AVOID":
            continue

        if (
            action == "USE"
            and avoid_detected
        ):
            continue

        for pattern in patterns:
            if re.search(
                pattern,
                lowered,
            ):
                result.add(
                    action
                )
                break

    return result

def evaluate_action_mapping(
    proposed_action,
    evidence_text,
):
    """
    제안된 structured action이 Evidence text에 의해
    어느 수준으로 지지되는지 판정합니다.

    Policy:
    - 같은 action이 명시적으로 등장하면 DIRECT
    - opposite action이 명시적으로 등장하면 CONFLICTING
    - action 표현은 없지만 관련 Evidence일 가능성만 있으면 PARTIAL
    - Evidence text가 없으면 NONE

    PARTIAL은 Safe Rendering에 사용할 수 없습니다.
    """
    if not isinstance(
        proposed_action,
        str,
    ):
        return NONE

    if not isinstance(
        evidence_text,
        str,
    ):
        return NONE

    text = evidence_text.strip()

    if not text:
        return NONE

    action = (
        proposed_action
        .strip()
        .upper()
    )

    evidence_actions = (
        detect_evidence_actions(
            text
        )
    )

    opposite = (
        _ACTION_OPPOSITES.get(
            action
        )
    )

    if (
        opposite
        and opposite in evidence_actions
    ):
        return CONFLICTING

    if action in evidence_actions:
        return DIRECT

    return PARTIAL


def evaluate_candidate_action(
    proposed_action,
    candidate,
    source_event,
):
    """
    Evidence Candidate 하나를 이용해 proposed action을 평가합니다.

    Safety boundary:
    - source_event가 다르면 NONE
    - Candidate 상태가 아니면 NONE
    - matched_tokens가 없으면 NONE
    - token match 자체는 DIRECT 근거가 아님
    """
    if not isinstance(
        candidate,
        dict,
    ):
        return NONE

    if (
        candidate.get("status")
        != "CANDIDATE"
    ):
        return NONE

    if (
        candidate.get("source_event")
        != source_event
    ):
        return NONE

    matched_tokens = candidate.get(
        "matched_tokens",
        [],
    )

    if not matched_tokens:
        return NONE

    return evaluate_action_mapping(
        proposed_action,
        candidate.get(
            "text",
            "",
        ),
    )


def combine_mapping_levels(
    levels,
):
    """
    여러 Evidence Candidate의 field-level mapping 결과를 합칩니다.

    Policy:
    - 하나라도 CONFLICTING이면 CONFLICTING
    - 하나라도 DIRECT이면 DIRECT
    - DIRECT 없이 PARTIAL만 있으면 PARTIAL
    - 아무 근거도 없으면 NONE

    Evidence 개수 자체로 level을 높이지 않습니다.
    """
    levels = list(
        levels
    )

    if CONFLICTING in levels:
        return CONFLICTING

    if DIRECT in levels:
        return DIRECT

    if PARTIAL in levels:
        return PARTIAL

    return NONE


def evaluate_action_candidates(
    proposed_action,
    candidates,
    source_event,
):
    """
    여러 Evidence Candidate를 사용해
    하나의 action field를 평가합니다.
    """
    levels = [
        evaluate_candidate_action(
            proposed_action,
            candidate,
            source_event,
        )
        for candidate in candidates
    ]

    return combine_mapping_levels(
        levels
    )