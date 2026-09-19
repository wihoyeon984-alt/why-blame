import textwrap
from narrative import synthesize_narrative

def render_card(file_name, line_range_str, repo_info, current_lines, timeline, stats):
    w = 64
    print("\nWHY-BLAME")
    print("━" * w)
    print(f"TARGET: {file_name}:{line_range_str}")
    if repo_info:
        owner, repo_name = repo_info
        print(f"REPO:   {owner}/{repo_name}")
    print("─" * w)

    # 1. CURRENT CODE
    print("CURRENT CODE")
    print("─" * w)
    for c_line in current_lines[:4]:
        disp = (c_line[:58] + "...") if len(c_line) > 61 else c_line
        print(f"> {disp}")
    print("─" * w)

    # 2. Evidence Sufficiency Guard (증거 부족 시 거절 카드)
    if stats.get("score", 0) <= 2:
        print("WHY (변경 사유)")
        print("─" * w)
        print("⚠️  No reliable historical explanation found.")
        print("   (수집된 역사적 근거가 부족하여 변경 사유를 확정할 수 없습니다.)\n")
        print("EVIDENCE")
        print("─" * w)
        print(f"[{'✓' if stats.get('has_message') else '✗'}] Commit message")
        print(f"[{'✓' if stats.get('has_diff') else '✗'}] Code diff (-/+)")
        print(f"[{'✓' if stats.get('has_refs') else '✗'}] Linked Issue / PR")
        print("─" * w)
        print(f"CONFIDENCE: LOW ({stats.get('strength', 'LOW')})")
        print("━" * w + "\n")
        return

    # 3. WHY (코드의 전기 및 정착 결론)
    headline, narrative_body = synthesize_narrative(timeline, stats)
    print("WHY (코드의 전기 및 정착 결론)")
    print("─" * w)
    print(f"* {headline}\n")
    for line in textwrap.wrap(narrative_body, width=62):
        print(f"  {line}")
    print("─" * w)

    # 4. HISTORY (타임라인 상세)
    print("HISTORY (타임라인 상세)")
    print("─" * w)
    for idx, item in enumerate(timeline):
        commit_short = item.get("hash", "")[:7]
        print(f"● {item.get('date', 'Unknown')}  {item.get('type', '')} ({commit_short})")
        print(f"  {item.get('message', '')[:60]}")

        for d in item.get("diff_lines", [])[:2]:
            print(f"  {d[:60]}")

        if item.get("ref_items"):
            for ref in item["ref_items"]:
                r_type = ref.get("type", "REF")
                r_num = ref.get("number", "")
                r_title = ref.get("title", "")
                r_context = ref.get("body_summary", "")
                r_url = ref.get("url", "")

                title_disp = f" ('{r_title[:28]}...')" if len(r_title) > 28 else (f" ('{r_title}')" if r_title else "")
                print(f"  ↳ {r_type} #{r_num}{title_disp}")

                if r_context:
                    print(f"    💬 Context: \"{r_context[:52]}...\"")
                if r_url:
                    print(f"    🔗 {r_url}")
        print()

    # 5. EVIDENCE CHECKLIST (증거 가용성 체크리스트)
    print("─" * w)
    print("EVIDENCE (수집된 근거 체크리스트)")
    print("─" * w)
    has_pr = any(any(r.get("type") == "PR" for r in t.get("ref_items", [])) for t in timeline)
    has_context = any(any(r.get("body_summary") for r in t.get("ref_items", [])) for t in timeline)
    has_issue = any(any(r.get("type") == "ISSUE" for r in t.get("ref_items", [])) for t in timeline)
    has_revert = stats.get("reverts_count", 0) > 0

    print(f"[{'✓' if stats.get('has_message') else '✗'}] Commit message (유의미한 커밋 메시지)")
    print(f"[{'✓' if stats.get('has_diff') else '✗'}] Code diff (물리적 코드 변경 증명)")
    print(f"[{'✓' if has_pr else '✗'}] Linked PR (GitHub 실제 머지 PR)")
    print(f"[{'✓' if has_context else '✗'}] PR / Issue Context (본문 상세 맥락)")
    if has_issue:
        print("[✓] Linked Issue (연관 이슈)")
    if has_revert:
        print(f"[✓] Revert History ({stats.get('reverts_count')}회 롤백 이력)")

    # 6. CONFIDENCE & LIMITATION
    print("─" * w)
    print(f"CONFIDENCE: {stats.get('grade', 'UNKNOWN')} ({stats.get('strength', '')})")
    print("─" * w)
    print("LIMITATION")
    print("─" * w)
    print("본 분석은 Git 히스토리 및 GitHub 공개 메타데이터를 근거로 복원되었습니다.")
    print("기록되지 않은 개발자의 실제 내적 의도는 자의적으로 단정하지 않습니다.")
    print("━" * w + "\n")