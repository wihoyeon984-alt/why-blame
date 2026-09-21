from claim_semantics import (
    CONFLICTING,
    DIRECT,
    NONE,
)


NO_CONTRADICTION = "NO_CONTRADICTION"


_ACTION_OPPOSITES = {
    "USE": "AVOID",
    "AVOID": "USE",
    "ENABLE": "DISABLE",
    "DISABLE": "ENABLE",
    "ADD": "REMOVE",
    "REMOVE": "ADD",
    "SET": "UNSET",
    "UNSET": "SET",
    "INCLUDE": "EXCLUDE",
    "EXCLUDE": "INCLUDE",
}


def normalize_action(action):
    """
    Structured semantic action을 비교 가능한 형태로 정규화합니다.

    모르는 action은 그대로 대문자로 보존합니다.
    """
    if not isinstance(action, str):
        return None

    value = action.strip().upper()

    if not value:
        return None

    return value


def actions_contradict(
    left_action,
    right_action,
):
    """
    두 structured action이 명시적인 반대 관계인지 판정합니다.

    token overlap이나 자연어 유사도는 사용하지 않습니다.
    등록된 polarity pair만 contradiction으로 판정합니다.
    """
    left = normalize_action(
        left_action
    )

    right = normalize_action(
        right_action
    )

    if not left or not right:
        return False

    return (
        _ACTION_OPPOSITES.get(left)
        == right
    )


def same_semantic_target(
    left,
    right,
):
    """
    두 Structured Claim이 같은 대상을 설명하는지
    보수적으로 확인합니다.

    v1에서는 subject와 target이 둘 다 존재할 때
    정확히 일치하는 경우만 같은 대상으로 간주합니다.

    불확실한 경우 contradiction이라고 추론하지 않습니다.
    """
    comparable_fields = []

    for field in (
        "subject",
        "target",
    ):
        left_value = left.get(field)
        right_value = right.get(field)

        if (
            left_value is None
            or right_value is None
        ):
            continue

        comparable_fields.append(
            left_value == right_value
        )

    if not comparable_fields:
        return False

    return all(
        comparable_fields
    )


def evaluate_contradiction(
    claim,
    evidence_semantics,
):
    """
    Structured Claim과 Evidence에서 추출된 Structured Semantics가
    명시적으로 충돌하는지 판정합니다.

    v1 Safety Policy:

    - 같은 semantic target이어야 함
    - action이 명시적인 opposite pair여야 함
    - 두 조건이 모두 만족할 때만 CONFLICTING
    - 판단할 수 없으면 NO_CONTRADICTION

    '충돌을 찾지 못함'은 'Claim이 증명됨'을 의미하지 않습니다.
    """
    if not isinstance(
        claim,
        dict,
    ):
        return NONE

    if not isinstance(
        evidence_semantics,
        dict,
    ):
        return NONE

    if not same_semantic_target(
        claim,
        evidence_semantics,
    ):
        return NO_CONTRADICTION

    if actions_contradict(
        claim.get("action"),
        evidence_semantics.get("action"),
    ):
        return CONFLICTING

    return NO_CONTRADICTION


def collect_contradictions(
    claim,
    evidence_items,
):
    """
    여러 Structured Evidence 중 Claim과 명시적으로
    충돌하는 Evidence만 반환합니다.

    각 결과에는 원본 Evidence와 contradiction 상태를 보존합니다.
    """
    result = []

    for item in evidence_items:
        semantics = item.get(
            "semantics"
        )

        status = evaluate_contradiction(
            claim,
            semantics,
        )

        if status != CONFLICTING:
            continue

        result.append(
            {
                "source": item.get(
                    "source"
                ),
                "ref": item.get(
                    "ref"
                ),
                "status": CONFLICTING,
                "semantics": semantics,
            }
        )

    return result

def contradiction_free(
    claim,
    evidence_items,
):
    """
    명시적인 contradiction이 하나도 없는지 반환합니다.

    True는 Evidence가 Claim을 entail한다는 뜻이 아닙니다.
    단지 현재 확인된 structured contradiction이 없다는 뜻입니다.
    """
    return not collect_contradictions(
        claim,
        evidence_items,
    )