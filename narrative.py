import textwrap

def synthesize_narrative(timeline, stats):
    """
    수집된 타임라인과 증거를 바탕으로 결정론적(규칙 기반) 서사 요약을 생성합니다.
    - 단일 커밋: 최초 관찰(Origin) 코드 서술
    - 롤백 이력 포함: 롤백 사유 및 최종 보완 정착 서사
    - 점진적 개선: 결함 수정 및 기능 추가 흐름 서술
    """
    if not timeline:
        return "추적 이력 없음", "추적된 Git 변경 이력이 없습니다."

    total = len(timeline)
    first = timeline[0]
    last = timeline[-1]
    reverts = [t for t in timeline if t.get("is_revert") or "REVERT" in t.get("type", "")]

    # 1. 원형 코드 (1회성 생성 후 변경 없음)
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

    # 2. 롤백(Revert) 이력이 포함된 복구/방어적 코드
    if reverts:
        headline = f"롤백({len(reverts)}회)을 거쳐 정착된 방어적 코드"
        revert_hashes = ", ".join(r.get("hash") for r in reverts)
        last_context = ""
        if last.get("ref_items"):
            ref = last["ref_items"][0]
            last_context = f" 특히 {ref.get('type', 'PR')} #{ref.get('number')}('{ref.get('title')}')을 통해"
        body = (
            f"확인된 이력상 {first.get('date')} 커밋({first.get('hash')})에서 처음 관찰된 이후, "
            f"수정 과정에서 부작용 등으로 롤백({revert_hashes})된 이력이 확인됩니다."
            f"{last_context} 최종 커밋({last.get('hash')})에서 문제가 보완되어 현재 형태로 정착되었습니다."
        )
        return headline, body

    # 3. 점진적 개선 및 결함 수정
    has_bug_fix = any("BUG FIX" in t.get("type", "") for t in timeline)
    key_types = list(dict.fromkeys(t.get("type", "").replace("📍 ", "").replace("✨ ", "").replace("🐛 ", "") for t in timeline[1:]))
    type_str = ", ".join(key_types[:2]) if key_types else "업데이트"

    if has_bug_fix:
        headline = f"결함 수정({type_str})을 거쳐 보강된 코드"
    else:
        headline = f"점진적 개선({type_str})을 거쳐 발전된 코드"

    all_refs = []
    for t in timeline:
        for r in t.get("ref_items", []):
            if r.get("title"):
                all_refs.append(f"{r.get('type', 'PR')} #{r.get('number')}('{r.get('title')}')")
    ref_part = f" ({', '.join(all_refs[:2])} 반영)" if all_refs else ""

    body = (
        f"확인된 이력상 {first.get('date')}에 처음 관찰된 이후, 총 {total}단계의 변경 이력이 확인되었습니다. "
        f"{last.get('date')} 최근 커밋({last.get('hash')})에서 '{last.get('message')}' 작업이 수행되며{ref_part} "
        f"현재 로직 구조로 보완되었습니다."
    )
    return headline, body