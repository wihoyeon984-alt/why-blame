import re
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from git_tracker import extract_git_history, get_repo_info, get_current_code_lines, get_file_line_count, is_git_repository
from github_client import fetch_ref_info, fetch_commit_prs
from timeline import build_timeline
from viewer import render_card
from json_renderer import render_json, render_json_error


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



def parse_output_mode(args):
    json_count = args.count("--json")

    if json_count > 1:
        raise ValueError(
            "--json ??? ? ?? ??? ? ????."
        )

    json_output = json_count == 1

    if not json_output:
        return list(args), False

    remaining_args = [
        arg
        for arg in args
        if arg != "--json"
    ]

    if any(
        arg in ("--version", "-V", "--help", "-h")
        for arg in remaining_args
    ):
        raise ValueError(
            "--json ??? ?? ?? ??? ??? "
            "?? ??? ? ????."
        )

    return remaining_args, True


def get_version():
    pyproject_path = Path(__file__).with_name("pyproject.toml")

    if pyproject_path.is_file():
        pyproject_text = pyproject_path.read_text(
            encoding="utf-8"
        )
        match = re.search(
            r'(?m)^version\s*=\s*"([^"]+)"\s*$',
            pyproject_text,
        )

        if match:
            return match.group(1)

    try:
        return version("why-blame")
    except PackageNotFoundError:
        return "unknown"


def main():
    args = sys.argv[1:]
    json_requested = "--json" in args

    try:
        args, json_output = parse_output_mode(
            args
        )

        if args in (["--version"], ["-V"]):
            print(f"why-blame {get_version()}")
            return

        parsed = parse_args(args)

    except ValueError as exc:
        if json_requested:
            render_json_error(
                "INVALID_ARGUMENTS",
                exc,
            )
        else:
            print(f"??: {exc}")
            print()
            print_usage()

        sys.exit(2)

    # --help / -h
    if parsed is None:
        print_usage()
        return

    file_name, start_line, end_line = parsed

    if not Path(file_name).is_file():
        message = (
            "The requested file does not exist: "
            + file_name
        )

        if json_output:
            render_json_error(
                "FILE_NOT_FOUND",
                message,
            )
        else:
            print(f"\uc624\ub958: {message}")

        sys.exit(1)

    file_line_count = get_file_line_count(
        file_name
    )

    if end_line > file_line_count:
        requested_range = (
            str(start_line)
            if start_line == end_line
            else f"{start_line}-{end_line}"
        )

        message = (
            "The requested line range "
            + requested_range
            + " exceeds the file length of "
            + str(file_line_count)
            + "."
        )

        if json_output:
            render_json_error(
                "LINE_RANGE_OUT_OF_BOUNDS",
                message,
            )
        else:
            print(f"??: {message}")

        sys.exit(1)

    if not is_git_repository():
        message = (
            "The current directory is not "
            "a Git repository."
        )

        if json_output:
            render_json_error(
                "NOT_A_GIT_REPOSITORY",
                message,
            )
        else:
            print(f"\uc624\ub958: {message}")

        sys.exit(1)

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
        if json_output:
            render_json_error(
                "NO_HISTORY",
                (
                    "No Git history was found for "
                    "the requested target."
                ),
            )

        sys.exit(1)

    timeline, stats = build_timeline(
        commits,
        repo_info,
        fetch_ref_info,
        fetch_commit_prs,
    )

    if json_output:
        render_json(
            file_name,
            start_line,
            end_line,
            repo_info,
            current_lines,
            timeline,
            stats,
        )
        return

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
