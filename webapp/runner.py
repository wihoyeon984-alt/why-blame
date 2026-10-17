import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLI_PATH = PROJECT_ROOT / "main.py"


class DashboardRunError(RuntimeError):
    """Raised when the dashboard cannot consume CLI output."""


@dataclass(frozen=True)
class AnalysisResult:
    exit_code: int
    document: dict


def build_target(file_path, start_line, end_line):
    if start_line == end_line:
        return f"{file_path}:{start_line}"

    return f"{file_path}:{start_line}-{end_line}"


def run_analysis(
    repository_path,
    file_path,
    start_line,
    end_line,
    timeout=60,
):
    repository = Path(repository_path).resolve()

    command = [
        sys.executable,
        str(CLI_PATH),
        build_target(
            file_path,
            start_line,
            end_line,
        ),
        "--json",
    ]

    try:
        result = subprocess.run(
            command,
            cwd=repository,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise DashboardRunError(
            "Why-Blame analysis timed out."
        ) from exc
    except OSError as exc:
        raise DashboardRunError(
            "Why-Blame analysis could not be started."
        ) from exc

    if result.stderr:
        raise DashboardRunError(
            "Why-Blame unexpectedly wrote to stderr."
        )

    try:
        output = result.stdout.decode("ascii")
    except UnicodeDecodeError as exc:
        raise DashboardRunError(
            "Why-Blame output was not ASCII-safe."
        ) from exc

    try:
        document = json.loads(output)
    except json.JSONDecodeError as exc:
        raise DashboardRunError(
            "Why-Blame did not return valid JSON."
        ) from exc

    if not isinstance(document, dict):
        raise DashboardRunError(
            "Why-Blame JSON must be an object."
        )

    if document.get("schema_version") != "1":
        raise DashboardRunError(
            "Unsupported Why-Blame JSON schema."
        )

    return AnalysisResult(
        exit_code=result.returncode,
        document=document,
    )
