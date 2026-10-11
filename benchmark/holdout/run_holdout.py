import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExecutionCase:
    case_id: str
    repository_url: str
    commit: str
    target_file: str
    start_line: int
    end_line: int


def _find_section_scalar(text, section, key):
    pattern = re.compile(
        rf"(?ms)^{re.escape(section)}:\s*$"
        rf"(.*?)"
        rf"(?=^[A-Za-z_][A-Za-z0-9_]*:\s*$|\Z)"
    )
    section_match = pattern.search(text)

    if not section_match:
        raise ValueError(
            f"missing section: {section}"
        )

    scalar_pattern = re.compile(
        rf'(?m)^\s{{2}}{re.escape(key)}:\s*'
        rf'["\x27]?([^"\x27]+?)["\x27]?\s*$'
    )
    scalar_match = scalar_pattern.search(
        section_match.group(1)
    )

    if not scalar_match:
        raise ValueError(
            f"missing {section}.{key}"
        )

    return scalar_match.group(1).strip()


def write_case_output(
    case_id,
    result,
    output_dir,
):
    output_dir = Path(output_dir)
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = output_dir / f"{case_id}.txt"

    parts = []

    if result.stdout:
        parts.append(result.stdout)

    if result.stderr:
        parts.append(result.stderr)

    rendered = "".join(parts)

    path.write_text(
        rendered,
        encoding="utf-8",
    )

    return path

def run_case(
    case,
    repository_dir,
    why_blame_main,
):
    repository_dir = Path(repository_dir)
    why_blame_main = Path(why_blame_main)

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    return subprocess.run(
        [
            sys.executable,
            str(why_blame_main),
            case.target_file,
            str(case.start_line),
            str(case.end_line),
        ],
        cwd=str(repository_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )

def run_candidate_case(
    case,
    repository_dir,
    why_blame_main,
    output_dir,
):
    prepare_repository(
        case.repository_url,
        case.commit,
        repository_dir,
    )

    result = run_case(
        case,
        repository_dir,
        why_blame_main,
    )

    return write_case_output(
        case.case_id,
        result,
        output_dir,
    )

def prepare_repository(
    repository_url,
    commit,
    destination,
):
    destination = Path(destination)

    subprocess.run(
        [
            "git",
            "clone",
            repository_url,
            str(destination),
        ],
        check=True,
    )

    subprocess.run(
        [
            "git",
            "-C",
            str(destination),
            "checkout",
            "--detach",
            commit,
        ],
        check=True,
    )

def discover_case_paths(cases_dir):
    cases_dir = Path(cases_dir)

    return [
        path
        for path in sorted(
            cases_dir.glob("*.yaml")
        )
        if path.name != "CASE_TEMPLATE.yaml"
    ]

def read_preserved_output(path):
    path = Path(path)
    data = path.read_bytes()

    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        return data.decode("utf-16")

    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig")

    return data.decode("utf-8")

def parse_preserved_target(output):
    if not isinstance(output, str):
        raise ValueError("preserved output must be a string")

    match = re.search(
        r"(?m)^TARGET:\s*(.+):(\d+)-(\d+)\s*$",
        output,
    )

    if not match:
        raise ValueError(
            "preserved output has no valid TARGET"
        )

    target_file = match.group(1).strip()
    start_line = int(match.group(2))
    end_line = int(match.group(3))

    if start_line < 1 or end_line < start_line:
        raise ValueError(
            "preserved TARGET has invalid line range"
        )

    return target_file, start_line, end_line

def resolve_preserved_target(
    first_output,
    current_output,
):
    first_target = parse_preserved_target(
        first_output
    )
    current_target = parse_preserved_target(
        current_output
    )

    if first_target != current_target:
        raise ValueError(
            "preserved TARGET artifacts disagree"
        )

    return first_target



def resolve_execution_case(
    case_path,
    first_output_path,
    current_output_path,
):
    try:
        return parse_execution_case(
            case_path
        )
    except ValueError:
        first_output = read_preserved_output(
            first_output_path
        )
        current_output = read_preserved_output(
            current_output_path
        )

        target_file, start_line, end_line = (
            resolve_preserved_target(
                first_output,
                current_output,
            )
        )

        text = Path(case_path).read_text(
            encoding="utf-8-sig"
        )

        case_id_match = re.search(
            r'(?m)^id:\s*["\x27]?([^"\x27]+?)["\x27]?\s*$',
            text,
        )
        if not case_id_match:
            raise ValueError("missing id")

        case_id = case_id_match.group(1).strip()

        yaml_target_file = _find_section_scalar(
            text,
            "target",
            "file",
        )

        if yaml_target_file != target_file:
            raise ValueError(
                f"{case_id}: preserved TARGET file disagrees with case"
            )

        return ExecutionCase(
            case_id=case_id,
            repository_url=_find_section_scalar(
                text,
                "repository",
                "url",
            ),
            commit=_find_section_scalar(
                text,
                "revision",
                "commit",
            ),
            target_file=target_file,
            start_line=start_line,
            end_line=end_line,
        )

def parse_execution_case(path):
    path = Path(path)

    text = path.read_text(
        encoding="utf-8-sig"
    )

    id_match = re.search(
        r'(?m)^id:\s*["\x27]?([^"\x27]+?)["\x27]?\s*$',
        text,
    )

    if not id_match:
        raise ValueError("missing id")

    case_id = id_match.group(1).strip()

    repository_url = _find_section_scalar(
        text,
        "repository",
        "url",
    )
    commit = _find_section_scalar(
        text,
        "revision",
        "commit",
    )
    target_file = _find_section_scalar(
        text,
        "target",
        "file",
    )
    start_line_text = _find_section_scalar(
        text,
        "target",
        "start_line",
    )
    end_line_text = _find_section_scalar(
        text,
        "target",
        "end_line",
    )

    try:
        start_line = int(start_line_text)
        end_line = int(end_line_text)
    except ValueError as exc:
        raise ValueError(
            f"{case_id}: target line range must be integers"
        ) from exc

    if start_line < 1 or end_line < start_line:
        raise ValueError(
            f"{case_id}: invalid target line range"
        )

    return ExecutionCase(
        case_id=case_id,
        repository_url=repository_url,
        commit=commit,
        target_file=target_file,
        start_line=start_line,
        end_line=end_line,
    )

def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(
        description="Run Why-Blame Holdout candidate cases."
    )
    parser.add_argument(
        "--cases-dir",
        type=Path,
        default=Path(__file__).parent / "cases",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent / "current_run",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path(__file__).parent / "candidate_repos",
    )
    parser.add_argument(
        "--why-blame-main",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "main.py",
    )

    args = parser.parse_args(argv)

    for case_path in discover_case_paths(
        args.cases_dir
    ):
        case = resolve_execution_case(
            case_path,
            Path(__file__).parent / "results" / f"{case_path.stem}.txt",
            Path(__file__).parent / "current_run" / f"{case_path.stem}.txt",
        )

        run_candidate_case(
            case,
            args.work_dir / case.case_id,
            args.why_blame_main,
            args.output_dir,
        )

    return args


if __name__ == "__main__":
    main()
