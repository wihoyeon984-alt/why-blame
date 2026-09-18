def render_card(file_name, line_range_str, repo_info, current_lines, timeline, stats):
    """Why-blame v2.0 카드를 화면에 출력합니다."""
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
    print("│ TIMELINE (시간순 발자취 + 코드 변경 Diff)              │")
    print("│                                                        │")

    for idx, item in enumerate(timeline):
        header = f"{item['date']}  {item['type']} ({item['hash']})"
        print(f"│ {header:<54} │")
        msg_disp = item["message"][:50]
        print(f"│   {msg_disp:<52} │")
        
        # [v2.0 신규] 실제 코드가 어떻게 바뀌었는지(- / +) 보여주기!
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
    print(f"│ • Evidence Strength: {stats['strength']:<34} │")
    print("└" + "─" * w + "┘")