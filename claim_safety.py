from claim_contradiction import (
    contradiction_free,
)
from claim_entailment import (
    evaluate_semantic_entailment,
)
from claim_semantics import (
    CONFLICTING,
    DIRECT,
)


SAFE_TO_RENDER = "SAFE_TO_RENDER"
BLOCK = "BLOCK"


def evaluate_semantic_safety(
    semantics,
    evidence_items=None,
):
    """
    Structured Claim을 강화된 자연어로 렌더링해도 되는지
    최종적으로 판정합니다.

    Safety Policy:

    - 전체 semantic entailment가 DIRECT여야 합니다.
    - structured contradiction이 없어야 합니다.
    - 둘 중 하나라도 만족하지 않으면 BLOCK합니다.

    중요한 원칙:
    - NO_CONTRADICTION만으로 Claim을 승인하지 않습니다.
    - Evidence가 많다는 이유만으로 승인하지 않습니다.
    - PARTIAL / INFERRED / NONE은 렌더링하지 않습니다.
    """
    evidence_items = list(
        evidence_items or []
    )

    entailment = evaluate_semantic_entailment(
        semantics
    )

    if entailment != DIRECT:
        return BLOCK

    if not contradiction_free(
        semantics,
        evidence_items,
    ):
        return BLOCK

    return SAFE_TO_RENDER


def with_semantic_safety(
    semantics,
    evidence_items=None,
):
    """
    Structured Claim의 복사본에 entailment와
    semantic safety 결과를 기록합니다.

    입력 semantics는 수정하지 않습니다.
    """
    result = dict(
        semantics
    )

    entailment = evaluate_semantic_entailment(
        semantics
    )

    safety = evaluate_semantic_safety(
        semantics,
        evidence_items,
    )

    result["entailment"] = entailment
    result["semantic_safety"] = safety

    return result


def collect_safe_semantics(
    semantics_items,
):
    """
    여러 Structured Claim 중 SAFE_TO_RENDER인 항목만 반환합니다.

    입력 형식:

    {
        "semantics": {...},
        "evidence_items": [...]
    }
    """
    result = []

    for item in semantics_items:
        semantics = item.get(
            "semantics"
        )

        evidence_items = item.get(
            "evidence_items",
            [],
        )

        if not isinstance(
            semantics,
            dict,
        ):
            continue

        evaluated = with_semantic_safety(
            semantics,
            evidence_items,
        )

        if (
            evaluated.get(
                "semantic_safety"
            )
            != SAFE_TO_RENDER
        ):
            continue

        result.append(
            evaluated
        )

    return result