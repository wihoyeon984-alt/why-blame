import sys
from git_tracker import extract_git_history, get_repo_info, get_current_code_lines
from github_client import fetch_title
from timeline import build_timeline
from viewer import render_card

args = sys.argv[1:]
if not args:
    print("사용법: python main.py <파일경로:줄번호> 또는 <파일경로:시작줄-끝줄>")
    print("예시:   python main.py service.py:1-3")
    sys.exit(1)

target = args[0]

# [v2.0 버그픽스] rsplit을 써서 C:\project\app.py:10 같은 윈도우 절대 경로도 완벽 지원!
if ":" in target:
    file_name, line_str = target.rsplit(":", 1)
    if "-" in line_str:
        s, e = line_str.split("-")
        start_line, end_line = int(s), int(e)
    else:
        start_line = int(line_str)
        end_line = start_line
elif len(args) >= 3:
    file_name = args[0]
    start_line = int(args)
    end_line = int(args)
elif len(args) == 2:
    file_name = args[0]
    start_line = int(args)
    end_line = int(args)
else:
    print("오류: 라인 번호를 지정해야 합니다. (예: service.py:1-3)")
    sys.exit(1)

line_range_str = f"{start_line}" if start_line == end_line else f"{start_line}-{end_line}"

current_lines = get_current_code_lines(file_name, start_line, end_line)
repo_info = get_repo_info()
commits = extract_git_history(file_name, start_line, end_line)

if not commits:
    sys.exit(1)

timeline, stats = build_timeline(commits, repo_info, fetch_title)
render_card(file_name, line_range_str, repo_info, current_lines, timeline, stats)