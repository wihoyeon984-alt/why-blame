def render_card(file_name, line_range_str, repo_info, current_lines, timeline, stats):
    w = 56
    print("┌" + "─" * w + "┐")
    print("│ 📜 WHY-BLAME v2.0                                      │")
    print(f"│ {file_name}:{line_range_str:<48} │")
    if repo_info:
        owner, repo_name = repo_info
        repo_display = f"{owner}/{repo_name}"
        print(f"│ 🌐 GitHub: {repo_display:<43} │")
    print("├" + "─" * w + "┤")
    print("│ CURRENT (현재 코드)                                    │")
    for c_line in current_lines[:4]:
        print(f"│ > {c_line[:50]:<50} │")
    print("├" + "─" * w + "┤")

    # ⚠️ [Evidence Sufficiency Guard] 증거 점수가 2점 이하(LOW)이면 거절 카드 출력
    if stats["score"] <= 2:
        print("│ WHY?                                                   │")
        print("│ No reliable historical explanation found.              │")
        print("│ (문서화된 근거가 없어 변경 사유를 확정할 수 없습니다.)  │")
        print("│                                                        │")
        print("│ Evidence Status                                        │")
        print("│ ✓ commit message                                       │")
        print(f"│ {'✓' if stats['has_diff'] else '✗'} code diff                                            │")
        print(f"│ {'✓' if stats['has_refs'] else '✗'} linked issue / PR                                   │")
        print("│ ✗ design discussion                                    │")
        print("│                                                        │")
        print(f"│ ⚠️ Evidence Strength: {stats['strength']:<32} │")
        print("│ * Evidence score is a heuristic, not a certainty.      │")
        print("└" + "─" * w + "┘")
        return

    # 증거가 충분할 때만 타임라인 상세 출력
    print("│ TIMELINE (시간순 발자취 + 코드 변경 Diff)              │")
    print("│                                                        │")

    for idx, item in enumerate(timeline):
        header = f"{item['date']}  {item['type']} ({item['hash']})"
        print(f"│ {header:<54} │")
        msg_disp = item["message"][:50]
        print(f"│   {msg_disp:<52} │")
        
        # 실제 코드 변경 Diff (- / +) 출력
        for d in item.get("diff_lines", [])[:2]:
            print(f"│     {d[:48]:<48} │")
        
        if item.get("ref_details"):
            ref_line = "   ↳ " + ", ".join(item["ref_details"])
            print(f"│ {ref_line[:53]:<54} │")
            
        if idx < len(timeline) - 1:
            print("│                          ↓                             │")

    print("│                                                        │")
    print("├" + "─" * w + "┤")
    print("│ EVIDENCE STRENGTH                                      │")
    print(f"│ • Total Events: {stats['total_events']}개                               │")
    print(f"│ • Reverts: {stats['reverts_count']}회                                  │")
    print(f"│ • Evidence Strength: {stats['strength']:<32} │")
    print("│ * Evidence score is a heuristic, not a certainty.      │")
    print("└" + "─" * w + "┘")