import subprocess
import re


def get_repo_info():
    """원격 GitHub 저장소 URL에서 (소유자, 저장소명)을 추출합니다."""
    res = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    remote_url = res.stdout.strip()

    if not remote_url:
        return None

    https_prefix = "https://github.com/"
    ssh_prefix = "git@github.com:"

    if remote_url.startswith(https_prefix):
        path = remote_url[len(https_prefix):]
    elif remote_url.startswith(ssh_prefix):
        path = remote_url[len(ssh_prefix):]
    else:
        return None

    if path.endswith(".git"):
        path = path[:-4]

    parts = path.split("/")

    if len(parts) != 2:
        return None

    owner, repo = parts

    if not owner or not repo:
        return None

    return owner, repo


def get_current_code_lines(file_name, start_line, end_line):
    """지정된 범위의 현재 코드 줄을 리스트로 읽어옵니다."""
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            lines = f.readlines()

        s = max(0, start_line - 1)
        e = min(len(lines), end_line)

        return [line.rstrip("\r\n") for line in lines[s:e]]

    except FileNotFoundError:
        print(f"오류: 파일을 찾을 수 없습니다: {file_name}")
        return []

    except Exception as e:
        print(f"오류: 파일 읽기 실패: {e}")
        return []


def extract_git_history(file_name, start_line, end_line):
    """
    git log -L을 실행해 커밋 정보와 실제 코드 변경 Diff(-/+)를 추출합니다.

    중요한 원칙:
    - Commit message와 Diff를 분리합니다.
    - Issue/PR 번호는 Commit message에서만 추출합니다.
    - Diff 내부의 '#123' 같은 문자열은 Issue/PR 참조로 취급하지 않습니다.
    - 전체 Commit SHA를 보존하여 GitHub API의 SHA 기반 PR 조회에 사용합니다.
    """

    cmd = [
        "git",
        "log",
        "-L",
        f"{start_line},{end_line}:{file_name}",
        "--no-merges",
        "--date=short",
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        print("Git history 추적 실패:")
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

        if not lines:
            continue

        # ---------------------------------------------------------
        # Commit SHA
        # ---------------------------------------------------------
        full_hash = lines[0].strip()

        if not full_hash:
            full_hash = "Unknown"

        # 화면 출력이나 짧은 식별에 사용할 7자리 SHA도 함께 보관합니다.
        short_hash = full_hash[:7]

        # ---------------------------------------------------------
        # Commit metadata / Diff 영역 분리
        # ---------------------------------------------------------
        if "diff --git" in block:
            header_part, diff_part = block.split("diff --git", 1)
        else:
            header_part, diff_part = block, ""

        header_lines = header_part.splitlines()

        # ---------------------------------------------------------
        # 날짜
        # ---------------------------------------------------------
        date_str = "Unknown"

        for line in header_lines:
            if line.startswith("Date:"):
                date_str = line.replace("Date:", "").strip()
                break

        # ---------------------------------------------------------
        # Commit message
        # ---------------------------------------------------------
        #
        # diff --git 이전의 4칸 들여쓰기 문자열만
        # Commit message로 취급합니다.
        #
        messages = [
            line.strip()
            for line in header_lines
            if line.startswith("    ")
        ]

        full_msg = " ".join(messages)

        # ---------------------------------------------------------
        # 실제 Diff
        # ---------------------------------------------------------
        #
        # + : 추가된 코드
        # - : 삭제된 코드
        #
        # +++ / --- 파일 헤더는 제외합니다.
        #
        diff_lines = []

        for line in diff_part.splitlines():

            if line.startswith("+") and not line.startswith("+++"):
                diff_lines.append("+ " + line[1:].strip())

            elif line.startswith("-") and not line.startswith("---"):
                diff_lines.append("- " + line[1:].strip())

        # ---------------------------------------------------------
        # Issue / PR 번호
        # ---------------------------------------------------------
        #
        # 반드시 Commit message에서만 찾습니다.
        # 따라서 Diff 내부의 '#999'를 Issue로 오인하지 않습니다.
        #
        numbers = re.findall(r"#(\d+)", full_msg)

        # ---------------------------------------------------------
        # Revert 여부
        # ---------------------------------------------------------
        #
        # 일반 Commit message 내부에 단순히 'revert'라는 단어가
        # 존재하는 것만으로 Revert Commit으로 판단하지 않습니다.
        #
        is_revert = full_msg.strip().lower().startswith("revert")

        commits.append(
            {
                "hash": full_hash,
                "short_hash": short_hash,
                "date": date_str,
                "message": full_msg,
                "diff_lines": diff_lines,
                "refs": numbers,
                "is_revert": is_revert,
            }
        )

    return commits