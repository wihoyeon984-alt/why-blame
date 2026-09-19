import sys
from git_tracker import extract_git_history, get_repo_info, get_current_code_lines
from github_client import fetch_ref_info, fetch_commit_prs
from timeline import build_timeline
from viewer import render_card

def main():
    args = sys.argv[1:]
    if not args:
        print("사용법: why-blame <파일경로:줄번호> 또는 <파일경로:시작줄-끝줄>")
        print("예시:    why-blame service.py:1-3")
        print("         why-blame service.py 1 3")
        sys.exit(1)

    target = args[0]

    # 1. 파일경로:줄번호 형식 (Windows 절대 경로 및 다중 라인 범위 지원)
    if ":" in target and target.rsplit(":", 1)[-1].replace("-", "").isdigit():
        file_name, line_str = target.rsplit(":", 1)
        if "-" in line_str:
            s, e = line_str.split("-", 1)
            start_line, end_line = int(s), int(e)
        else:
            start_line = int(line_str)
            end_line = start_line

    # 2. 공백으로 시작줄 끝줄 지정 (예: why-blame service.py 1 3)
    elif len(args) >= 3:
        file_name, start_str, end_str = args[:3]
        start_line = int(start_str)
        end_line = int(end_str)

    # 3. 공백으로 단일 라인 지정 (예: why-blame service.py 10)
    elif len(args) == 2:
        file_name, line_str = args[:2]
        start_line = int(line_str)
        end_line = start_line

    else:
        print("오류: 라인 번호를 지정해야 합니다. (예: service.py:1-3 또는 service.py 1 3)")
        sys.exit(1)

    line_range_str = f"{start_line}" if start_line == end_line else f"{start_line}-{end_line}"

    current_lines = get_current_code_lines(file_name, start_line, end_line)
    repo_info = get_repo_info()
    commits = extract_git_history(file_name, start_line, end_line)

    if not commits:
        sys.exit(1)

    # SHA 기반 PR 탐색 함수와 번호 기반 이슈 탐색 함수를 함께 전달
    timeline, stats = build_timeline(commits, repo_info, fetch_ref_info, fetch_commit_prs)
    render_card(file_name, line_range_str, repo_info, current_lines, timeline, stats)

if __name__ == "__main__":
    main()