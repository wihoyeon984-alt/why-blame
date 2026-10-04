from claim_semantics import (
    CONFLICTING,
    DIRECT,
    INFERRED,
    NONE,
    PARTIAL,
    get_field_evidence,
    get_present_fields,
)


def evaluate_field_entailment(
    semantics,
    field,
):
    """
    하나의 semantic field에 연결된 Evidence를 평가합니다.

    Safety policy:
    - CONFLICTING Evidence가 하나라도 있으면 CONFLICTING
    - DIRECT Evidence가 하나라도 있으면 DIRECT
    - PARTIAL Evidence가 하나라도 있으면 PARTIAL
    - INFERRED Evidence만 있으면 INFERRED
    - Evidence가 없으면 NONE

    Evidence 개수는 강도를 자동으로 높이지 않습니다.
    """
    evidence = get_field_evidence(
        semantics,
        field,
    )

    if not evidence:
        return NONE

    levels = {
        item.get("level", NONE)
        for item in evidence
    }

    if CONFLICTING in levels:
        return CONFLICTING

    if DIRECT in levels:
        return DIRECT

    if PARTIAL in levels:
        return PARTIAL

    if INFERRED in levels:
        return INFERRED

    return NONE


def evaluate_semantic_entailment(
    semantics,
):
    """
    Structured Claim 전체의 entailment를 계산합니다.

    현재 v1에서는 값이 존재하는 semantic field를 모두
    Claim의 의미 구성요소로 취급합니다.

    Policy:
    - 한 field라도 CONFLICTING이면 전체 CONFLICTING
    - 한 field라도 NONE이면 전체 NONE
    - 한 field라도 INFERRED이면 전체 INFERRED
    - 한 field라도 PARTIAL이면 전체 PARTIAL
    - 모든 present field가 DIRECT이면 전체 DIRECT
    - semantic field 자체가 없으면 NONE
    """
    fields = get_present_fields(
        semantics
    )

    if not fields:
        return NONE

    results = {
        field: evaluate_field_entailment(
            semantics,
            field,
        )
        for field in fields
    }

    levels = set(
        results.values()
    )

    if CONFLICTING in levels:
        return CONFLICTING

    if NONE in levels:
        return NONE

    if INFERRED in levels:
        return INFERRED

    if PARTIAL in levels:
        return PARTIAL

    if levels == {DIRECT}:
        return DIRECT

    return NONE


def with_entailment(
    semantics,
):
    """
    Structured Claim의 복사본에 field별 entailment와
    전체 entailment 결과를 기록합니다.

    입력 semantics는 수정하지 않습니다.
    """
    result = dict(
        semantics
    )

    fields = get_present_fields(
        semantics
    )

    result["field_entailment"] = {
        field: evaluate_field_entailment(
            semantics,
            field,
        )
        for field in fields
    }

    result["entailment"] = (
        evaluate_semantic_entailment(
            semantics
        )
    )

    return result


def is_safe_for_semantic_rendering(
    semantics,
):
    """
    현재 v1에서 자연어 semantic rendering을 허용할 수 있는
    최소 조건을 판정합니다.

    DIRECT만 허용합니다.

    PARTIAL / INFERRED / NONE / CONFLICTING은 아직
    강화된 자연어 Claim으로 렌더링하지 않습니다.
    """
    return (
        evaluate_semantic_entailment(
            semantics
        )
        == DIRECT
    )
