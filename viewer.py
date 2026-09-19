def render_card(file_name, line_range_str, repo_info, current_lines, timeline, stats):
    w = 58
    print("┌" + "─" * w + "┐")
    print("│ WHY-BLAME v2.1 (Evidence-First Architecture)           │")
    print(f"│ Target: {file_name}:{line_range_str:<47}│")
    if repo_info:
        owner, repo_name = repo_info
        repo_display = f"{owner}/{repo_name}"
        print(f"│ GitHub: {repo_display:<49}│")
    print("├" + "─" * w + "┤")
    print("│ CURRENT (현재 코드 라인)                               │")
    for c_line in current_lines[:4]:
        print(f"│ > {c_line[:52]:<54}│")
    print("├" + "─" * w + "┤")

    # [Evidence Sufficiency Guard] 증거 점수가 2점 이하(LOW)이면 거절 카드 출력
    if stats["score"] <= 2:
        print("│ WHY?                                                   │")
        print("│ No reliable historical explanation found.              │")
        print("│ (신뢰할 만한 근거가 부족하여 변경 사유를 확정할 수 없습니다.) │")
        print("│                                                        │")
        print("│ Evidence Status:                                       │")
        print("│ [ ] commit message                                     │")
        print(f"│ [{'x' if stats['has_diff'] else ' '}] code diff                                      │")
        print(f"│ [{'x' if stats['has_refs'] else ' '}] linked issue / PR                               │")
        print("│ [ ] design discussion                                  │")
        print("│                                                        │")
        print(f"│ Evidence Strength: {stats['strength']:<36}│")
        print("│ * Evidence score is a heuristic, not a certainty.      │")
        print("└" + "─" * w + "┘")
        return

    # 증거가 충분할 때의 타임라인 상세 출력
    print("│ TIMELINE (변경 이력 & Diff & GitHub 참조)             │")
    print("│                                                        │")

    for idx, item in enumerate(timeline):
        header = f"{item['date']} {item['type']} ({item['hash']})"
        print(f"│ {header:<56}│")
        msg_disp = item["message"][:52]
        print(f"│   {msg_disp:<54}│")

        # Diff (- / +) 출력
        for d in item.get("diff_lines", [])[:2]:
            print(f"│   {d[:52]:<54}│")

        # 구조화된 PR / Issue 정보 및 링크 출력
        if item.get("ref_items"):
            for ref in item["ref_items"]:
                r_type = ref.get("type", "REF")
                r_num = ref.get("number", "")
                r_title = ref.get("title", "")
                r_url = ref.get("url", "")
                
                title_disp = f" ('{r_title[:28]}...')" if len(r_title) > 28 else (f" ('{r_title}')" if r_title else "")
                ref_line = f"   ↳ {r_type} #{r_num}{title_disp}"
                print(f"│ {ref_line:<56}│")
                if r_url:
                    url_line = f"     🔗 {r_url}"
                    print(f"│ {url_line[:56]:<56}│")
        elif item.get("ref_details"):
            ref_line = "   ↳ " + ", ".join(item["ref_details"])
            print(f"│ {ref_line[:56]:<56}│")

        if idx < len(timeline) - 1:
            print("│                                                        │")

    print("│                                                        │")
    print("├" + "─" * w + "┤")
    print("│ EVIDENCE STRENGTH (증거 종합 평가)                     │")
    print(f"│ Total Events: {stats['total_events']:<43}│")
    print(f"│ Reverts: {stats['reverts_count']:<48}│")
    print(f"│ Evidence Strength: {stats['strength']:<36}│")
    print("│ * Evidence score is a heuristic, not a certainty.      │")
    print("└" + "─" * w + "┘")