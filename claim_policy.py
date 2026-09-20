from claim_evidence import (
    CONFLICTING,
    REVERT_CAUSE,
    SUPPORTED,
)


DIRECT = "DIRECT"
CONSERVATIVE = "CONSERVATIVE"
HIDDEN = "HIDDEN"


HIGH_CONFIDENCE = {
    "VERY HIGH",
    "HIGH",
}

MEDIUM_CONFIDENCE = {
    "MEDIUM",
    "MODERATE",
}


def get_claim_visibility(claim, stats):
    """
    Claim을 Narrative에 노출할 수 있는지 결정합니다.

    Safety Policy:

    1. SUPPORTED가 아니면 숨깁니다.
    2. CONFLICTING Claim은 항상 숨깁니다.
    3. 전체 Evidence가 blocked 상태면 숨깁니다.
    4. Consistency가 INCONSISTENT이면 숨깁니다.
    5. REVERT_CAUSE는 SUPPORTED여도 보수적으로 처리합니다.
    6. HIGH / VERY HIGH Confidence에서는 직접 표현할 수 있습니다.
    7. MEDIUM / MODERATE에서는 보수적으로 표현합니다.
    8. WEAK / LOW / unknown Confidence에서는 숨깁니다.
    """
    if claim.get("status") == CONFLICTING:
        return HIDDEN

    if claim.get("status") != SUPPORTED:
        return HIDDEN

    if stats.get("is_blocked") is True:
        return HIDDEN

    consistency = (
        stats.get("consistency") or ""
    ).upper()

    if consistency == "INCONSISTENT":
        return HIDDEN

    confidence = (
        stats.get("confidence") or ""
    ).upper()

    if claim.get("type") == REVERT_CAUSE:
        if confidence in HIGH_CONFIDENCE:
            return CONSERVATIVE

        return HIDDEN

    if confidence in HIGH_CONFIDENCE:
        return DIRECT

    if confidence in MEDIUM_CONFIDENCE:
        return CONSERVATIVE

    return HIDDEN


def collect_visible_claims(claims, stats):
    """
    Claim 리스트에서 Narrative에 노출 가능한 Claim만 반환합니다.

    반환되는 각 Claim에는 visibility 필드가 추가됩니다.
    입력 Claim 자체는 수정하지 않습니다.
    """
    visible = []

    for claim in claims:
        visibility = get_claim_visibility(
            claim,
            stats,
        )

        if visibility == HIDDEN:
            continue

        item = dict(claim)
        item["visibility"] = visibility

        visible.append(item)

    return visible