def synthesize_narrative(timeline, stats):
    """
    수집된 타임라인의 사건을 바탕으로 보수적인 변경 이력 서사를 생성한다.

    원칙:
    - 증거가 불일치하면 구체적인 WHY 생성을 차단한다.
    - Git/GitHub 기록에서 확인 가능한 내용만 표현한다.
    - BUG FIX, FEATURE, REVERT 등의 중간 변경 이력을 보존한다.
    - "방어적", "보강된", "발전된"처럼 증거 이상의 평가적 표현은 피한다.
    """
    if not timeline:
        return (
            "추적 이력 없음",
            "추적할 Git 변경 이력이 없습니다.",
        )

    # False-WHY 방어:
    # 증거가 충돌하면 구체적인 변경 사유를 생성하지 않는다.
    if (
        stats.get("is_blocked") is True
        or stats.get("consistency") == "INCONSISTENT"
    ):
        pairs_str = ", ".join(stats.get("inconsistent_pairs", []))

        headline = "⚠️ 증거 불일치(Inconsistent Evidence) 감지"

        body = (
            "수집된 커밋 메시지와 연관 PR의 맥락이 서로 상충되거나 "
            f"다른 주제를 가리키고 있습니다 ({pairs_str}). "
            "거짓 서사 생성을 방지하기 위해 구체적인 변경 사유를 "
            "단정하지 않으며, 신뢰도(Confidence)가 강등되었습니다."
        )

        return headline, body

    total = len(timeline)
    first = timeline[0]
    last = timeline[-1]

    # 단일 커밋만 존재하는 경우
    if total == 1:
        headline = "현재 확인된 이력상 변경 단계가 하나인 코드"

        first_ref = ""

        if first.get("ref_items"):
            ref = first["ref_items"][0]
            ref_type = ref.get("type", "참조")
            ref_number = ref.get("number")
            ref_title = ref.get("title")

            first_ref = (
                f" 연관 {ref_type} #{ref_number}"
                f"('{ref_title}')가 확인됩니다."
            )

        body = (
            f"현재 확인된 Git 이력상 {first.get('date', '초기')} "
            f"커밋({first.get('hash')})에서 처음 관찰되었습니다. "
            "이후 추가적인 변경 이력은 확인되지 않습니다."
            f"{first_ref}"
        )

        return headline, body

    reverts = [
        item
        for item in timeline
        if item.get("is_revert")
        or "REVERT" in item.get("type", "")
    ]

    bug_fixes = [
        item
        for item in timeline[1:]
        if "BUG FIX" in item.get("type", "")
    ]

    mid_commits = timeline[1:-1]
    mid_parts = []

    if mid_commits:
        mid_bugs = [
            item
            for item in mid_commits
            if "BUG FIX" in item.get("type", "")
        ]

        mid_reverts = [
            item
            for item in mid_commits
            if item.get("is_revert")
            or "REVERT" in item.get("type", "")
        ]

        mid_features = [
            item
            for item in mid_commits
            if "FEATURE" in item.get("type", "")
        ]

        if mid_bugs:
            hashes = ", ".join(
                item.get("hash", "")
                for item in mid_bugs
            )

            mid_parts.append(
                f"결함 수정 {len(mid_bugs)}회({hashes})"
            )

        if mid_reverts:
            revert_details = ", ".join(
                f"{item.get('hash', '')} "
                f"('{item.get('message', '')}')"
                for item in mid_reverts
            )

            mid_parts.append(
                f"롤백 {len(mid_reverts)}회({revert_details})"
            )

        if mid_features:
            hashes = ", ".join(
                item.get("hash", "")
                for item in mid_features
            )

            mid_parts.append(
                f"기능 추가 {len(mid_features)}회({hashes})"
            )

    mid_summary = ", ".join(mid_parts)

    if mid_summary:
        mid_sentence = (
            f"이후 {mid_summary} 등의 변경 단계를 거쳤습니다. "
        )
    elif mid_commits:
        mid_sentence = (
            f"이후 중간 {len(mid_commits)}단계의 변경을 거쳤습니다. "
        )
    else:
        mid_sentence = ""

    last_context = ""
    last_change = "변경 사항"

    if last.get("ref_items"):
        ref = last["ref_items"][0]

        last_context = (
            f"PR #{ref.get('number')}"
            f"('{ref.get('title')}')을 통해 "
        )

        last_change = "확인 가능한 변경 사항"

    body = (
        f"확인된 이력상 {first.get('date')} "
        f"커밋({first.get('hash')})에서 처음 관찰되었습니다. "
        f"{mid_sentence}"
        f"최종적으로 {last.get('date')} "
        f"커밋({last.get('hash')})에서 "
        f"{last_context}{last_change}이 반영되어 "
        "현재 형태로 정착되었습니다."
    )

    # Headline 역시 관찰 가능한 이력만 표현한다.
    if reverts:
        headline = (
            f"롤백({len(reverts)}회)을 포함한 변경 이력을 거쳐 "
            "현재 형태로 정착된 코드"
        )

    elif bug_fixes:
        headline = (
            f"결함 수정({len(bug_fixes)}회)을 포함한 변경 이력을 거쳐 "
            "현재 형태로 정착된 코드"
        )

    else:
        headline = (
            f"총 {total}단계의 변경 이력을 거쳐 "
            "현재 형태로 정착된 코드"
        )

    return headline, body