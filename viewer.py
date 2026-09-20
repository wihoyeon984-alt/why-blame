import textwrap

from narrative import synthesize_narrative


def render_card(
    file_name,
    line_range_str,
    repo_info,
    current_lines,
    timeline,
    stats,
):
    width = 64
    thick_line = "━" * width
    thin_line = "─" * width

    print("\nWHY-BLAME")
    print(thick_line)

    print(f"TARGET: {file_name}:{line_range_str}")

    if repo_info:
        owner, repo_name = repo_info
        print(f"REPO:   {owner}/{repo_name}")

    print(thin_line)

    # ---------------------------------------------------------
    # 1. CURRENT CODE
    # ---------------------------------------------------------
    print("CURRENT CODE")
    print(thin_line)

    for code_line in current_lines[:4]:
        display = (
            code_line[:58] + "..."
            if len(code_line) > 61
            else code_line
        )

        print(f"> {display}")

    print(thin_line)

    # ---------------------------------------------------------
    # 2. Evidence Sufficiency Guard
    # ---------------------------------------------------------
    if stats.get("score", 0) <= 2:
        print("WHY (변경 이유)")
        print(thin_line)

        print(
            "⚠️  신뢰할 수 있는 변경 사유를 "
            "확정하기 어렵습니다."
        )

        print(
            "   수집된 역사적 Evidence가 부족하여 "
            "구체적인 WHY를 생성하지 않습니다.\n"
        )

        print("EVIDENCE EVALUATION")
        print(thin_line)

        message_mark = (
            "✓"
            if stats.get("has_message")
            else "✗"
        )

        diff_mark = (
            "✓"
            if stats.get("has_diff")
            else "✗"
        )

        refs_mark = (
            "✓"
            if stats.get("has_refs")
            else "✗"
        )

        print(
            f"[{message_mark}] Commit message"
        )

        print(
            f"[{diff_mark}] Code diff (-/+)"
        )

        print(
            f"[{refs_mark}] Linked Issue / PR"
        )

        print(thin_line)

        print(
            "CONFIDENCE: LOW "
            f"({stats.get('strength', 'LOW')})"
        )

        print(thick_line + "\n")

        return

    # ---------------------------------------------------------
    # 3. WHY
    # ---------------------------------------------------------
    headline, narrative_body = synthesize_narrative(
        timeline,
        stats,
    )

    print("WHY (코드의 변경 이력과 정착 과정)")
    print(thin_line)

    print(f"* {headline}\n")

    for line in textwrap.wrap(
        narrative_body,
        width=62,
    ):
        print(f"  {line}")

    print(thin_line)

    # ---------------------------------------------------------
    # 4. HISTORY
    # ---------------------------------------------------------
    print("HISTORY (타임라인 상세)")
    print(thin_line)

    for item in timeline:
        commit_short = item.get(
            "hash",
            "",
        )[:7]

        print(
            f"● {item.get('date', 'Unknown')}  "
            f"{item.get('type', '')} "
            f"({commit_short})"
        )

        print(
            f"  {item.get('message', '')[:60]}"
        )

        for diff_line in item.get(
            "diff_lines",
            [],
        )[:2]:
            print(
                f"  {diff_line[:60]}"
            )

        if item.get("ref_items"):
            for ref in item["ref_items"]:
                ref_type = ref.get(
                    "type",
                    "REF",
                )

                ref_number = ref.get(
                    "number",
                    "",
                )

                ref_title = ref.get(
                    "title",
                    "",
                )

                ref_context = ref.get(
                    "body_summary",
                    "",
                )

                ref_url = ref.get(
                    "url",
                    "",
                )

                if len(ref_title) > 28:
                    title_display = (
                        f" ('{ref_title[:28]}...')"
                    )

                elif ref_title:
                    title_display = (
                        f" ('{ref_title}')"
                    )

                else:
                    title_display = ""

                print(
                    f"  ↳ {ref_type} "
                    f"#{ref_number}"
                    f"{title_display}"
                )

                if ref_context:
                    print(
                        "    💬 Context: "
                        f"\"{ref_context[:52]}...\""
                    )

                if ref_url:
                    print(
                        f"    🔗 {ref_url}"
                    )

        print()

    # ---------------------------------------------------------
    # 5. EVIDENCE EVALUATION
    # ---------------------------------------------------------
    print(thin_line)

    print(
        "EVIDENCE EVALUATION "
        "(4차원 신뢰도 지표)"
    )

    print(thin_line)

    has_pr = any(
        any(
            ref.get("type") == "PR"
            for ref in item.get(
                "ref_items",
                [],
            )
        )
        for item in timeline
    )

    has_context = stats.get(
        "has_context",
        False,
    )

    has_issue = any(
        any(
            ref.get("type") == "ISSUE"
            for ref in item.get(
                "ref_items",
                [],
            )
        )
        for item in timeline
    )

    message_mark = (
        "✓"
        if stats.get("has_message")
        else "✗"
    )

    diff_mark = (
        "✓"
        if stats.get("has_diff")
        else "✗"
    )

    pr_mark = (
        "✓"
        if has_pr
        else "✗"
    )

    context_mark = (
        "✓"
        if has_context
        else "✗"
    )

    print(
        f"[{message_mark}] "
        "Commit message "
        "(유의미한 커밋 메시지)"
    )

    print(
        f"[{diff_mark}] "
        "Code diff "
        "(물리적 코드 변경 증명)"
    )

    print(
        f"[{pr_mark}] "
        "Linked PR "
        "(GitHub에서 확인된 PR)"
    )

    print(
        f"[{context_mark}] "
        "PR Context "
        "(본문 상세 맥락)"
    )

    if has_issue:
        print(
            "[✓] Linked Issue "
            "(연결된 이슈)"
        )

    print(thin_line)

    print(
        "COVERAGE:    "
        f"{stats.get('coverage', 'N/A')} "
        f"({stats.get('strength', '')})"
    )

    consistency = stats.get(
        "consistency",
        "N/A",
    )

    if consistency == "INCONSISTENT":
        print(
            "CONSISTENCY: ⚠️ INCONSISTENT "
            "(Commit과 PR의 맥락 충돌)"
        )

    elif consistency == "HIGH":
        print(
            "CONSISTENCY: ✓ HIGH "
            "(도메인 및 변경 맥락 일치)"
        )

    elif consistency == "MODERATE":
        print(
            "CONSISTENCY: △ MODERATE "
            "(부분 일치 또는 추가 검증 필요)"
        )

    else:
        print(
            f"CONSISTENCY: {consistency}"
        )

    print(
        "AMBIGUITY:   "
        f"{stats.get('ambiguity', 'LOW')}"
    )

    print(
        "CONFIDENCE:  "
        f"{stats.get(
            'confidence',
            stats.get(
                'grade',
                'UNKNOWN',
            ),
        )}"
    )

    print(thin_line)

    # ---------------------------------------------------------
    # 6. LIMITATION
    # ---------------------------------------------------------
    print("LIMITATION")
    print(thin_line)

    limitations = stats.get(
        "limitations",
        [],
    )

    if limitations:
        for limitation in limitations:
            print(
                f"- {limitation}"
            )

    print(
        "본 분석은 Git History와 GitHub 공개 메타데이터를 "
        "근거로 복원되었습니다."
    )

    print(
        "기록되지 않은 개발자의 실제 의도는 "
        "자의적으로 단정하지 않습니다."
    )

    print(thick_line + "\n")