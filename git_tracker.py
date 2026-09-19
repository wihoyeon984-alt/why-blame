import subprocess
import re

def get_repo_info():
    """원격 저장소 URL에서 (소유자, 저장소명)을 추출합니다."""
    res = subprocess.run(["git", "config", "--get", "remote.origin.url"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    remote_url = res.stdout.strip()
    if not remote_url:
        return None
    m = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", remote_url)
    if m:
        return m.group(1), m.group(2)
    return None

def get_current_code_lines(file_name, start_line, end_line):
    """지정된 범위의 현재 코드 줄들을 리스트로 읽어옵니다."""
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            lines = f.readlines()
        s = max(0, start_line - 1)
        e = min(len(lines), end_line)
        return [l.rstrip("\r\n") for l in lines[s:e]]
    except FileNotFoundError:
        print(f"오류: 파일을 찾을 수 없습니다: {file_name}")
        return []
    except Exception as e:
        print(f"오류: 파일 읽기 실패: {e}")
        return []

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
        lines = block.splitlines()
        commit_hash = lines[0][:7]
        
        date_str = "Unknown"
        for l in lines:
            if l.startswith("Date:"):
                date_str = l.replace("Date:", "").strip()

        messages = [l.strip() for l in lines if l.startswith("    ")]
        full_msg = " ".join(messages)
        
        # [v2.0 신규] 실제 코드 Diff (-와 +) 추출
        diff_lines = []
        in_diff = False
        for l in lines:
            if l.startswith("diff --git"):
                in_diff = True
                continue
            if in_diff:
                if l.startswith("+") and not l.startswith("+++"):
                    diff_lines.append("+ " + l[1:].strip())

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
