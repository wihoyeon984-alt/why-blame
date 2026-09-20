def normalize_confidence(stats):
    """
    Confidence Model v2의 여러 confidence 표현을
    Narrative Policy가 사용하는 공통 단계로 정규화한다.
    """
    raw = str(
        stats.get(
            "confidence",
            stats.get(
                "overall_confidence",
                stats.get("grade", "UNKNOWN"),
            ),
        )
    ).strip().upper()

    if raw.startswith("VERY HIGH"):
        return "VERY_HIGH"

    if raw.startswith("HIGH"):
        return "HIGH"

    if raw.startswith("MEDIUM") or raw.startswith("MODERATE"):
        return "MODERATE"

    if raw.startswith("WEAK"):
        return "WEAK"

    if raw.startswith("LOW"):
        return "LOW"

    return "UNKNOWN"


def get_narrative_policy(stats):
    """
    Confidence 결과를 Narrative 표현 정책으로 변환한다.

    정책:
    - BLOCKED: 증거 충돌. 구체적인 WHY 차단
    - LIMITED: 증거 부족. 구체적인 WHY 제한
    - CONSERVATIVE: 확인된 이력 중심
    - EVIDENCE_BASED: 검증된 외부 근거 범위에서만 구체화

    Confidence가 높더라도 증거에 없는 원인을 생성할 수는 없다.
    """
    if (
        stats.get("is_blocked") is True
        or stats.get("consistency") == "INCONSISTENT"
    ):
        return "BLOCKED"

    confidence = normalize_confidence(stats)

    if confidence in ("LOW", "WEAK"):
        return "LIMITED"

    if confidence in ("MODERATE", "UNKNOWN"):
        return "CONSERVATIVE"

    if confidence in ("HIGH", "VERY_HIGH"):
        return "EVIDENCE_BASED"

    return "CONSERVATIVE"


def get_verified_ref(item):
    """
    Timeline item에서 Narrative에 사용할 수 있는
    검증 가능한 외부 근거를 하나 반환한다.

    NOT_FOUND 상태의 reference는 근거로 사용하지 않는다.
    """
    for ref in item.get("ref_items", []):
        if ref.get("status") == "NOT_FOUND":
            continue

        title = ref.get("title")

        if not title:
            continue

        return ref

    return None


def synthesize_narrative(timeline, stats):
    """
    Timeline과 Confidence Model의 결과를 바탕으로
    증거 수준에 맞는 보수적인 Narrative를 생성한다.

    핵심 원칙:
    - WHY는 생성하는 것이 아니라 증거로부터 도출한다.
    - 증거가 충돌하면 구체적인 WHY를 생성하지 않는다.
    - 증거가 부족하면 변경 사유를 확정하지 않는다.
    - Confidence가 낮을수록 Narrative도 보수적으로 표현한다.
    - Confidence가 높아도 증거에 없는 원인을 추론하지 않는다.
    """
    if not timeline:
        return (
            "추적 이력 없음",
            "추적할 Git 변경 이력이 없습니다.",
        )

    policy = get_narrative_policy(stats)
    confidence = normalize_confidence(stats)

    # ---------------------------------------------------------
    # 1. BLOCKED
    # ---------------------------------------------------------
    if policy == "BLOCKED":
        pairs_str = ", ".join(
            stats.get("inconsistent_pairs", [])
        )

        headline = "⚠️ 증거 불일치로 변경 사유를 확정할 수 없음"

        if pairs_str:
            body = (
                "수집된 커밋 메시지와 연관 PR/Issue의 맥락이 "
                "서로 일치하지 않습니다. "
                f"충돌이 확인된 근거: {pairs_str}. "
                "False-WHY 생성을 방지하기 위해 구체적인 "
                "변경 사유를 제시하지 않습니다."
            )
        else:
            body = (
                "수집된 변경 이력에서 서로 일치하지 않는 "
                "근거가 확인되었습니다. "
                "False-WHY 생성을 방지하기 위해 구체적인 "
                "변경 사유를 제시하지 않습니다."
            )

        return headline, body

    # ---------------------------------------------------------
    # 2. LOW / WEAK
    # ---------------------------------------------------------
    if policy == "LIMITED":
        first = timeline[0]
        last = timeline[-1]

        headline = "신뢰할 수 있는 변경 사유를 확정하기 어려움"

        if len(timeline) == 1:
            body = (
                f"Git 이력상 {first.get('date', '날짜 미상')} "
                f"커밋({first.get('hash', '')})이 확인되지만, "
                "변경 사유를 뒷받침할 충분한 외부 근거가 없습니다. "
                "따라서 구체적인 WHY는 생성하지 않습니다."
            )
        else:
            body = (
                f"Git 이력상 {first.get('date', '날짜 미상')} "
                f"커밋({first.get('hash', '')})부터 "
                f"{last.get('date', '날짜 미상')} "
                f"커밋({last.get('hash', '')})까지 "
                f"총 {len(timeline)}단계의 변경이 확인됩니다. "
                "그러나 변경 사유를 충분히 검증할 외부 근거가 "
                "부족하므로 구체적인 WHY는 생성하지 않습니다."
            )

        return headline, body

    total = len(timeline)
    first = timeline[0]
    last = timeline[-1]

    # ---------------------------------------------------------
    # 3. 단일 Commit
    # ---------------------------------------------------------
    if total == 1:
        verified_ref = get_verified_ref(first)

        headline = "현재 확인된 이력상 변경 단계가 하나인 코드"

        body = (
            f"현재 확인된 Git 이력상 "
            f"{first.get('date', '날짜 미상')} "
            f"커밋({first.get('hash', '')})에서 "
            "처음 관찰되었습니다."
        )

        if (
            policy == "EVIDENCE_BASED"
            and verified_ref is not None
        ):
            ref_type = verified_ref.get("type", "REF")
            ref_number = verified_ref.get("number")
            ref_title = verified_ref.get("title")

            body += (
                f" 연관 {ref_type} #{ref_number}"
                f"('{ref_title}')가 외부 근거로 확인됩니다."
            )
        else:
            body += (
                " 이후 추가적인 변경 사유를 확정할 수 있는 "
                "근거는 제한적입니다."
            )

        return headline, body

    # ---------------------------------------------------------
    # 4. Timeline Facts
    # ---------------------------------------------------------
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
            f"이후 중간 {len(mid_commits)}단계의 "
            "변경을 거쳤습니다. "
        )

    else:
        mid_sentence = ""

    # ---------------------------------------------------------
    # 5. Final event
    # ---------------------------------------------------------
    verified_ref = get_verified_ref(last)

    last_sentence = (
        f"최종적으로 {last.get('date', '날짜 미상')} "
        f"커밋({last.get('hash', '')})에서 "
        "현재 형태의 변경이 관찰됩니다."
    )

    # HIGH / VERY HIGH에서만 외부 근거를 구체적으로 연결한다.
    if (
        policy == "EVIDENCE_BASED"
        and verified_ref is not None
    ):
        ref_type = verified_ref.get("type", "REF")
        ref_number = verified_ref.get("number")
        ref_title = verified_ref.get("title")

        last_sentence = (
            f"최종적으로 {last.get('date', '날짜 미상')} "
            f"커밋({last.get('hash', '')})에서 "
            f"{ref_type} #{ref_number}('{ref_title}')와 "
            "연결된 변경이 확인되며, "
            "현재 형태의 변경이 관찰됩니다."
        )

    # MODERATE / MEDIUM에서는 reference가 있더라도
    # 구체적인 원인으로 확대하지 않는다.
    elif policy == "CONSERVATIVE":
        last_sentence = (
            f"최종적으로 {last.get('date', '날짜 미상')} "
            f"커밋({last.get('hash', '')})까지의 "
            "변경 이력이 확인되며, "
            "구체적인 변경 원인은 확인된 이력의 범위를 "
            "넘어 단정하지 않습니다."
        )

    body = (
        f"확인된 이력상 {first.get('date', '날짜 미상')} "
        f"커밋({first.get('hash', '')})에서 "
        f"처음 관찰되었습니다. "
        f"{mid_sentence}"
        f"{last_sentence}"
    )

    # ---------------------------------------------------------
    # 6. Evidence-only Headline
    # ---------------------------------------------------------
    if reverts:
        headline = (
            f"롤백({len(reverts)}회)을 포함한 변경 이력을 거쳐 "
            "현재 형태에 이른 코드"
        )

    elif bug_fixes:
        headline = (
            f"결함 수정({len(bug_fixes)}회)을 포함한 "
            "변경 이력이 확인된 코드"
        )

    else:
        headline = (
            f"총 {total}단계의 변경 이력이 확인된 코드"
        )

    # Confidence를 문장에 직접 삽입하지 않는다.
    # Viewer의 CONFIDENCE 영역에서 별도로 표시되며,
    # Narrative에서는 Confidence를 표현 정책으로만 사용한다.
    _ = confidence

    return headline, body