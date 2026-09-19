def synthesize_narrative(timeline, stats):
    """
    수집된 타임라인의 모든 사건을 바탕으로 결정론적 서사를 생성합니다.
    - 증거 불일치(INCONSISTENT) 감지 시 거짓 서사 생성을 차단하고 경고 출력
    - 롤백 시 실제 커밋 메시지를 직접 인용
    - 중간 단계(결함 수정, 기능 추가 등)를 빠짐없이 서사에 반영
    """
    if not timeline:
        return "추적 이력 없음", "추적된 Git 변경 이력이 없습니다."

    # [핵심 방어] 증거 불일치 감지 시 거짓 서사 생성 원천 차단!
    if (
        stats.get("is_blocked") is True
        or stats.get("consistency") == "INCONSISTENT"
    ):
        pairs_str = ", ".join(stats.get("inconsistent_pairs", []))
        headline = "⚠️ 증거 불일치(Inconsistent Evidence) 감지"
        body = (
            f"수집된 커밋 메시지와 연관 PR의 맥락이 서로 상충되거나 다른 주제를 가리키고 있습니다 ({pairs_str}). "
            f"거짓 서사 생성을 방지하기 위해 구체적인 변경 사유를 단정하지 않으며, 신뢰도(Confidence)가 강등되었습니다."
        )
        return headline, body

    total = len(timeline)
    first = timeline[0]
    last = timeline[-1]

    if total == 1:
        headline = "현재 확인된 이력상 변경 없는 원형(Origin) 코드"
        first_ref = ""
        if first.get("ref_items"):
            ref = first["ref_items"][0]
            first_ref = f" (연관 {ref.get('type', '참조')} #{ref.get('number')}: '{ref.get('title')}')"
        body = (
            f"현재 확인된 Git 이력상 {first.get('date', '초기')} 커밋({first.get('hash')})에서 처음 관찰되었으며, "
            f"이후 추가적인 수정 이력은 확인되지 않았습니다{first_ref}."
        )
        return headline, body

    reverts = [t for t in timeline if t.get("is_revert") or "REVERT" in t.get("type", "")]
    bug_fixes = [t for t in timeline[1:] if "BUG FIX" in t.get("type", "")]

    mid_commits = timeline[1:-1]
    mid_parts = []
    if mid_commits:
        mid_bugs = [t for t in mid_commits if "BUG FIX" in t.get("type", "")]
        mid_revs = [t for t in mid_commits if t.get("is_revert") or "REVERT" in t.get("type", "")]
        mid_feats = [t for t in mid_commits if "FEATURE" in t.get("type", "")]

        if mid_bugs:
            mid_parts.append(f"결함 수정 {len(mid_bugs)}회({', '.join(b.get('hash') for b in mid_bugs)})")
        if mid_revs:
            rev_strs = [f"{r.get('hash')} ('{r.get('message')}')" for r in mid_revs]
            mid_parts.append(f"롤백 {len(mid_revs)}회({', '.join(rev_strs)})")
        if mid_feats:
            mid_parts.append(f"기능 추가 {len(mid_feats)}회({', '.join(f.get('hash') for f in mid_feats)})")

    mid_summary = ", ".join(mid_parts)
    if mid_summary:
        mid_sentence = f"이후 {mid_summary} 등의 변경 단계를 거쳤습니다. "
    elif mid_commits:
        mid_sentence = f"이후 중간 {len(mid_commits)}단계의 수정을 거쳤습니다. "
    else:
        mid_sentence = ""

    last_context = ""
    last_change = "변경 사항"

    if last.get("ref_items"):
        ref = last["ref_items"][0]
        last_context = f"PR #{ref.get('number')}('{ref.get('title')}')을 통해 "
        last_change = "검증된 변경 사항"

    body = (
        f"확인된 이력상 {first.get('date')} 커밋({first.get('hash')})에서 처음 관찰되었습니다. "
        f"{mid_sentence}"
        f"최종적으로 {last.get('date')} 커밋({last.get('hash')})에서 "
        f"{last_context}{last_change}이 반영되어 현재 형태로 정착되었습니다."
    )

    if reverts:
        headline = f"롤백({len(reverts)}회) 및 보완을 거쳐 정착된 방어적 코드"
    elif bug_fixes:
        headline = f"결함 수정({len(bug_fixes)}회)을 거쳐 보강된 코드"
    else:
        headline = f"총 {total}단계 변경을 거쳐 발전된 코드"

    return headline, body