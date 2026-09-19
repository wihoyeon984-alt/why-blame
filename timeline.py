def calculate_evidence_strength(timeline):
    """
    가중치 매트릭스 (총점 12점 만점)
    - 유의미한 커밋 메시지 (+2)
    - 코드 Diff (-/+) 존재 (+2)
    - Issue/PR 참조 번호 (+3)
    - GitHub 실제 메타데이터 확인 (+2)
    - Revert 이력 (+3)
    합계: 2 + 2 + 3 + 2 + 3 = 12점 만점
    """
    score = 0
    total = len(timeline)
    reverts = sum(1 for t in timeline if t.get("is_revert"))
    has_diff = any(len(t.get("diff_lines", [])) > 0 for t in timeline)
    has_refs = any(len(t.get("refs", [])) > 0 for t in timeline)
    has_fetched = any(
        any(ref.get("title") for ref in t.get("ref_items", []))
        or any("'" in r for r in t.get("ref_details", []))
        for t in timeline
    )
    # 5글자 이상의 정상 커밋 메시지가 존재하는지 여부
    has_message = total > 0 and any(len(t.get("message", "")) > 5 for t in timeline)

    if has_message:
        score += 2
    if has_diff:
        score += 2
    if has_refs:
        score += 3
    if has_fetched:
        score += 2
    if reverts > 0:
        score += 3

    if score >= 11:
        grade = "VERY HIGH"
    elif score >= 8:
        grade = "HIGH"
    elif score >= 5:
        grade = "MODERATE"
    elif score >= 3:
        grade = "WEAK"
    else:
        grade = "LOW"

    return {
        "score": score,
        "grade": grade,
        "total_events": total,
        "reverts_count": reverts,
        "has_diff": has_diff,
        "has_refs": has_refs,
        "has_message": has_message,
        "strength": f"{grade} [{score}/12점]"
    }