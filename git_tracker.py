def extract_git_history(file_name, start_line, end_line):
    """git log -L을 실행해 커밋 정보와 실제 코드 변경 Diff(-/+)를 추출합니다."""
    cmd = ["git", "log", "-L", f"{start_line},{end_line}:{file_name}", "--no-merges", "--date=short"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    
    if result.returncode != 0:
        print("❌ Git history 추적 실패:")
        print(result.stderr.strip())
        return []

    raw_log = result.stdout
    if not raw_log.strip():
        return []

    commits = []
    for block in raw_log.split("commit "):
        if not block.strip():
            continue

        # [핵심 수정] diff --git을 기준으로 커밋 메타데이터 영역과 Diff 영역을 엄격히 분리!
        if "diff --git" in block:
            header_part, diff_part = block.split("diff --git", 1)
        else:
            header_part, diff_part = block, ""

        header_lines = header_part.splitlines()
        commit_hash = header_lines[0][:7] if header_lines else "Unknown"
        
        date_str = "Unknown"
        for l in header_lines:
            if l.startswith("Date:"):
                date_str = l.replace("Date:", "").strip()

        # 커밋 메시지는 반드시 diff --git 이전 줄(4칸 들여쓰기)에서만 수집!
        messages = [l.strip() for l in header_lines if l.startswith("    ")]
        full_msg = " ".join(messages)

        # 실제 코드 Diff는 diff_part에서만 추출! (코드 주석 #123 등이 메시지에 섞이지 않음)
        diff_lines = []
        for l in diff_part.splitlines():
            if l.startswith("+") and not l.startswith("+++"):
                diff_lines.append("+ " + l[1:].strip())
            elif l.startswith("-") and not l.startswith("---"):
                diff_lines.append("- " + l[1:].strip())

        # 오염 없는 순수 커밋 메시지에서만 Issue/PR 번호 및 Revert 판별
        numbers = re.findall(r"#(\d+)", full_msg)
        is_revert = "revert" in full_msg.lower()
        
        commits.append({
            "hash": commit_hash,
            "date": date_str,
            "message": full_msg,
            "diff_lines": diff_lines,
            "refs": numbers,
            "is_revert": is_revert
        })
    return commits