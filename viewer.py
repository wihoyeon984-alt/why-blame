import textwrap
from narrative import synthesize_narrative

def render_card(file_name, line_range_str, repo_info, current_lines, timeline, stats):
    w = 60
    print("┌" + "─" * w + "┐")
    print("│ WHY-BLAME v2.3 (Biography & Evidence Architecture)       │")
    print(f"│ Target: {file_name}:{line_range_str:<49}│")
    if repo_info:
        owner, repo_name = repo_info
        repo_display = f"{owner}/{repo_name}"
        print(f"│ GitHub: {repo_display:<51}│")
    print("├" + "─" * w + "┤")
    print("│ CURRENT (현재 코드 라인)                                 │")
    for c_line in current_lines[:4]:
        print(f"│ > {c_line[:54]:<56}│")
    print("├" + "─" * w + "┤")

    # [Evidence Sufficiency Guard] 증거 점수 부족 시 거절 카드 출력
    if stats["score"] <= 2:
        print("│ WHY?                                                     │")
        print("│ No reliable historical explanation found.                │")
        print("│ (신뢰할 만한 근거가 부족하여 변경 사유를 확정할 수 없습니다.)   │")
        print("│                                                          │")
        print("│ Evidence Status:                                         │")
        print(f"│ [{'x' if stats.get('has_message') else ' '}] commit message                                     │")
        print(f"│ [{'x' if stats['has_diff'] else ' '}] code diff                                        │")
        print(f"│ [{'x' if stats['has_refs'] else ' '}] linked issue / PR                                 │")
        print("│ [ ] design discussion                                    │")
        print("│                                                          │")
        print(f"│ Evidence Strength: {stats['strength']:<38}│")
        print("│ * Evidence score is a heuristic, not a certainty.        │")
        print("└" + "─" * w + "┘")
        return

    # 📖 BIOGRAPHY: 코드의 전기 및 변경 사유 서사 요약문
    headline, narrative_body = synthesize_narrative(timeline, stats)
    print("│ 📖 BIOGRAPHY (코드의 전기 및 정착 사유)                 │")
    print(f"│  * {headline:<54}│")
    print("│                                                          │")
    for line in textwrap.wrap(narrative_body, width=54):
        print(f"│  {line:<56}│")
    print("├" + "─" * w + "┤")

    # 타임라인 상세 출력
    print("│ TIMELINE (변경 이력 & Diff & GitHub 참조)               │")
    print("│                                                          │")

    for idx, item in enumerate(timeline):
        header = f"{item['date']} {item['type']} ({item['hash']})"
        print(f"│ {header:<58}│")
        msg_disp = item["message"][:54]
        print(f"│   {msg_disp:<56}│")

        # 실제 Diff (- / +) 출력
        for d in item.get("diff_lines", [])[:2]:
            print(f"│   {d[:54]:<56}│")

        # 구조화된 PR / Issue 정보 및 링크
        if item.get("ref_items"):
            for ref in item["ref_items"]:
                r_type = ref.get("type", "REF")
                r_num = ref.get("number", "")
                r_title = ref.get("title", "")
                r_context = ref.get("body_summary", "")
                r_labels = ref.get("labels", [])
                r_url = ref.get("url", "")

                title_disp = f" ('{r_title[:28]}...')" if len(r_title) > 28 else (f" ('{r_title}')" if r_title else "")
                ref_line = f"   ↳ {r_type} #{r_num}{title_disp}"
                print(f"│ {ref_line:<58}│")

                if r_context:
                    ctx_line = f"     💬 Context: \"{r_context[:44]}...\""
                    print(f"│ {ctx_line:<58}│")

                if r_labels:
                    lbl_str = ", ".join(r_labels[:3])
                    lbl_line = f"     🏷️ Labels: [{lbl_str}]"
                    print(f"│ {lbl_line:<58}│")

                if r_url:
                    url_line = f"     🔗 {r_url}"
                    print(f"│ {url_line[:58]:<58}│")

        elif item.get("ref_details"):
            ref_line = "   ↳ " + ", ".join(item["ref_details"])
            print(f"│ {ref_line:<58}│")

        if idx < len(timeline) - 1:
            print("│                                                          │")

    print("│                                                          │")
    print("├" + "─" * w + "┤")
    print("│ EVIDENCE STRENGTH (증거 종합 평가)                       │")
    print(f"│ Total Events: {stats['total_events']:<45}│")
    print(f"│ Reverts: {stats['reverts_count']:<50}│")
    print(f"│ Evidence Strength: {stats['strength']:<38}│")
    print("│ * Evidence score is a heuristic, not a certainty.        │")
    print("└" + "─" * w + "┘")