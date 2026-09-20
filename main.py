import sys

from git_tracker import extract_git_history, get_repo_info, get_current_code_lines
from github_client import fetch_ref_info, fetch_commit_prs
from timeline import build_timeline
from viewer import render_card


USAGE = """사용법:
  why-blame <파일경로:줄번호>
  why-blame <파일경로:시작줄-끝줄>
  why-blame <파일경로> <줄번호>
  why-blame <파일경로> <시작줄> <끝줄>

예시:
  why-blame service.py:10
  why-blame service.py:1-3
  why-blame service.py 10
  why-blame service.py 1 3
"""


def print_usage():
    print(USAGE)


def validate_line_range(start_line, end_line):
    if start_line < 1 or end_line < 1:
        raise ValueError("라인 번호는 1 이상이어야 합니다.")

    if start_line > end_line:
        raise ValueError("시작 라인은 끝 라인보다 클 수 없습니다.")


def parse_args(args):
    if not args:
        raise ValueError("분석할 파일과 라인 번호를 지정해야 합니다.")

    if args[0] in ("-h", "--help"):
        return None

    target = args[0]

    # why-blame service.py:10
    # why-blame service.py:1-3
    if ":" in target:
        file_part, line_part = target.rsplit(":", 1)

        if file_part and line_part:
            if "-" in line_part:
                start_str, end_str = line_part.split("-", 1)

                if start_str.isdigit() and end_str.isdigit():
                    start_line = int(start_str)
                    end_line = int(end_str)

                    validate_line_range(start_line, end_line)

                    return file_part, start_line, end_line

            elif line_part.isdigit():
                start_line = int(line_part)

                validate_line_range(start_line, start_line)

                return file_part, start_line, start_line

    # why-blame service.py 1 3
    if len(args) == 3:
        file_name, start_str, end_str = args

        if not start_str.isdigit() or not end_str.isdigit():
            raise ValueError("라인 번호는 양의 정수여야 합니다.")

        start_line = int(start_str)
        end_line = int(end_str)

        validate_line_range(start_line, end_line)

        return file_name, start_line, end_line

    # why-blame service.py 10
    if len(args) == 2:
        file_name, line_str = args

        if not line_str.isdigit():
            raise ValueError("라인 번호는 양의 정수여야 합니다.")

        start_line = int(line_str)

        validate_line_range(start_line, start_line)

        return file_name, start_line, start_line

    raise ValueError(
        "올바른 입력 형식이 아닙니다. "
        "예: service.py:1-3 또는 service.py 1 3"
    )


def main():
    args = sys.argv[1:]

    try:
        parsed = parse_args(args)

    except ValueError as exc:
        print(f"오류: {exc}")
        print()
        print_usage()
        sys.exit(2)

    # --help / -h
    if parsed is None:
        print_usage()
        return

    file_name, start_line, end_line = parsed

    line_range_str = (
        f"{start_line}"
        if start_line == end_line
        else f"{start_line}-{end_line}"
    )

    current_lines = get_current_code_lines(
        file_name,
        start_line,
        end_line,
    )

    repo_info = get_repo_info()

    commits = extract_git_history(
        file_name,
        start_line,
        end_line,
    )

    if not commits:
        sys.exit(1)

    timeline, stats = build_timeline(
        commits,
        repo_info,
        fetch_ref_info,
        fetch_commit_prs,
    )

    render_card(
        file_name,
        line_range_str,
        repo_info,
        current_lines,
        timeline,
        stats,
    )


if __name__ == "__main__":
    main()