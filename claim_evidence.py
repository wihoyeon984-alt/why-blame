SUPPORTED = "SUPPORTED"
UNVERIFIED = "UNVERIFIED"
CONFLICTING = "CONFLICTING"

BEHAVIOR = "BEHAVIOR"
CAUSE = "CAUSE"
REVERT_FACT = "REVERT_FACT"
REVERT_CAUSE = "REVERT_CAUSE"


def make_claim(text, claim_type, evidence=None):
    """
    Claim-level Evidence 평가에 사용할 기본 구조를 생성합니다.
    """
    return {
        "text": text,
        "type": claim_type,
        "status": UNVERIFIED,
        "evidence": list(evidence or []),
    }


def make_evidence(source, ref, supports=True):
    """
    하나의 Claim에 연결할 Evidence 항목을 생성합니다.

    supports:
        True  -> Claim을 지지
        False -> Claim과 충돌
    """
    return {
        "source": source,
        "ref": ref,
        "supports": supports,
    }


def evaluate_claim(claim):
    """
    Claim에 연결된 Evidence를 기준으로 상태를 판정합니다.

    v1 Safety Policy:

    1. 충돌 Evidence가 하나라도 있으면 CONFLICTING
    2. REVERT_CAUSE는 별도의 원인 Evidence가 없으면 UNVERIFIED
    3. BEHAVIOR는 DIFF Evidence가 직접 지지하면 SUPPORTED
    4. REVERT_FACT는 REVERT Evidence가 직접 지지하면 SUPPORTED
    5. CAUSE는 COMMIT / PR / ISSUE 중 최소 하나의 직접 지지가 필요
    6. 그 외에는 UNVERIFIED
    """
    evidence = claim.get("evidence", [])

    if any(
        item.get("supports") is False
        for item in evidence
    ):
        claim["status"] = CONFLICTING
        return claim

    supporting_sources = {
        item.get("source")
        for item in evidence
        if item.get("supports") is True
    }

    claim_type = claim.get("type")

    if claim_type == BEHAVIOR:
        if "DIFF" in supporting_sources:
            claim["status"] = SUPPORTED
        else:
            claim["status"] = UNVERIFIED

        return claim

    if claim_type == CAUSE:
        if supporting_sources.intersection(
            {"COMMIT", "PR", "ISSUE"}
        ):
            claim["status"] = SUPPORTED
        else:
            claim["status"] = UNVERIFIED

        return claim

    if claim_type == REVERT_FACT:
        if "REVERT" in supporting_sources:
            claim["status"] = SUPPORTED
        else:
            claim["status"] = UNVERIFIED

        return claim

    if claim_type == REVERT_CAUSE:
        if supporting_sources.intersection(
            {"COMMIT", "PR", "ISSUE"}
        ):
            claim["status"] = SUPPORTED
        else:
            claim["status"] = UNVERIFIED

        return claim

    claim["status"] = UNVERIFIED
    return claim


def collect_supported_claims(claims):
    """
    SUPPORTED 상태인 Claim만 반환합니다.
    """
    result = []

    for claim in claims:
        evaluated = evaluate_claim(claim)

        if evaluated["status"] == SUPPORTED:
            result.append(evaluated)

    return result