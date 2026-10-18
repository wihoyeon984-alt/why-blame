"""Safely capture a Holdout v2 current-main evaluation snapshot."""

from dataclasses import dataclass
import hashlib
import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path




@dataclass(frozen=True)
class CommandResult:
    """Exact result captured from one subprocess."""

    command: tuple
    working_directory: str
    exit_code: int
    stdout: bytes
    stderr: bytes
    started_at_utc: str
    finished_at_utc: str




@dataclass(frozen=True)
class RepositoryCheckout:
    """Verified checkout of one frozen external repository."""

    repository_path: str
    requested_commit: str
    checked_out_commit: str


class SnapshotError(ValueError):
    """Raised when a snapshot cannot be created safely."""


@dataclass(frozen=True)
class ExecutionSpec:
    """Frozen execution input for one Holdout v2 case."""

    case_id: str
    repository_url: str
    repository_commit: str
    target_file: str
    start_line: int
    end_line: int

    @property
    def target(self):
        return (
            f"{self.target_file}:"
            f"{self.start_line}-"
            f"{self.end_line}"
        )


def sha256_file(path):
    """Return the uppercase SHA-256 of a file's exact bytes."""

    digest = hashlib.sha256()

    with Path(path).open("rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest().upper()


def build_file_manifest(root):
    """Build a stable manifest for all files below root."""

    root = Path(root).resolve()

    if not root.is_dir():
        raise SnapshotError(
            f"manifest root is not a directory: {root}"
        )

    entries = []

    files = sorted(
        item
        for item in root.rglob("*")
        if item.is_file()
    )

    for path in files:
        relative_path = (
            path.resolve()
            .relative_to(root)
            .as_posix()
        )

        entries.append(
            {
                "relative_path": relative_path,
                "length": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )

    return entries


def ensure_new_output_directory(path):
    """Create a new snapshot directory without overwriting."""

    path = Path(path)

    if path.exists():
        raise SnapshotError(
            f"snapshot output already exists: {path}"
        )

    path.mkdir(
        parents=True,
        exist_ok=False,
    )

    return path


def _read_json(path):
    path = Path(path)

    try:
        text = path.read_text(
            encoding="utf-8-sig",
        )
        document = json.loads(text)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SnapshotError(
            f"cannot read JSON artifact: {path}"
        ) from exc

    if not isinstance(document, dict):
        raise SnapshotError(
            f"JSON artifact must be an object: {path}"
        )

    return document


def _require_string(document, key, artifact_name):
    value = document.get(key)

    if not isinstance(value, str) or not value:
        raise SnapshotError(
            f"{artifact_name}.{key} is required"
        )

    return value


def _require_positive_integer(
    document,
    key,
    artifact_name,
):
    value = document.get(key)

    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 1
    ):
        raise SnapshotError(
            f"{artifact_name}.{key} must be a positive integer"
        )

    return value


def load_execution_specs(holdout_dir):
    """Load frozen cases and their selected execution targets."""

    holdout_dir = Path(holdout_dir)
    cases_dir = holdout_dir / "cases"
    candidates_dir = holdout_dir / "candidates"

    if not cases_dir.is_dir():
        raise SnapshotError(
            f"cases directory does not exist: {cases_dir}"
        )

    if not candidates_dir.is_dir():
        raise SnapshotError(
            f"candidates directory does not exist: {candidates_dir}"
        )

    specs = []

    for case_path in sorted(cases_dir.glob("*.json")):
        case_id = case_path.stem
        candidate_path = (
            candidates_dir
            / f"{case_id}.json"
        )

        if not candidate_path.is_file():
            raise SnapshotError(
                f"candidate does not exist: {case_id}"
            )

        case = _read_json(case_path)
        candidate = _read_json(candidate_path)

        if case.get("case_id") != case_id:
            raise SnapshotError(
                f"case id mismatch: {case_id}"
            )

        if candidate.get("candidate_id") != case_id:
            raise SnapshotError(
                f"candidate id mismatch: {case_id}"
            )

        if case.get("frozen") is not True:
            raise SnapshotError(
                f"case is not frozen: {case_id}"
            )

        repository = case.get("repository")

        if not isinstance(repository, dict):
            raise SnapshotError(
                f"case.repository is required: {case_id}"
            )

        candidate_repository = candidate.get(
            "repository"
        )

        if not isinstance(candidate_repository, dict):
            raise SnapshotError(
                f"candidate.repository is required: {case_id}"
            )

        repository_url = _require_string(
            repository,
            "url",
            "case.repository",
        )

        repository_commit = _require_string(
            repository,
            "commit",
            "case.repository",
        )

        if (
            candidate_repository.get("url")
            != repository_url
            or candidate_repository.get("commit")
            != repository_commit
        ):
            raise SnapshotError(
                f"repository mismatch: {case_id}"
            )

        target = candidate.get("target")

        if not isinstance(target, dict):
            raise SnapshotError(
                f"candidate.target is required: {case_id}"
            )

        target_file = _require_string(
            target,
            "file",
            "candidate.target",
        )

        target_path = Path(target_file)

        if target_path.is_absolute() or ".." in target_path.parts:
            raise SnapshotError(
                f"unsafe target path: {case_id}"
            )

        start_line = _require_positive_integer(
            target,
            "start_line",
            "candidate.target",
        )

        end_line = _require_positive_integer(
            target,
            "end_line",
            "candidate.target",
        )

        if start_line > end_line:
            raise SnapshotError(
                f"reversed target range: {case_id}"
            )

        specs.append(
            ExecutionSpec(
                case_id=case_id,
                repository_url=repository_url,
                repository_commit=repository_commit,
                target_file=target_file,
                start_line=start_line,
                end_line=end_line,
            )
        )

    if not specs:
        raise SnapshotError(
            "no Holdout v2 cases found"
        )

    return specs

def run_command(
    command,
    working_directory,
    environment=None,
):
    """Run a command and preserve exact stdout and stderr bytes."""

    command = tuple(
        str(item)
        for item in command
    )

    if not command:
        raise SnapshotError(
            "command must not be empty"
        )

    working_directory = Path(
        working_directory
    ).resolve()

    if not working_directory.is_dir():
        raise SnapshotError(
            "working directory does not exist: "
            f"{working_directory}"
        )

    process_environment = os.environ.copy()

    if environment:
        process_environment.update(
            {
                str(key): str(value)
                for key, value in environment.items()
            }
        )

    started_at = datetime.now(timezone.utc)

    try:
        completed = subprocess.run(
            list(command),
            cwd=working_directory,
            env=process_environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise SnapshotError(
            f"command could not start: {command[0]}"
        ) from exc

    finished_at = datetime.now(timezone.utc)

    return CommandResult(
        command=command,
        working_directory=str(
            working_directory
        ),
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        started_at_utc=started_at.isoformat(),
        finished_at_utc=finished_at.isoformat(),
    )


def require_success(result, operation):
    """Reject a failed command with a bounded diagnostic."""

    if result.exit_code == 0:
        return result

    diagnostic = result.stderr.decode(
        "utf-8",
        errors="replace",
    ).strip()

    if len(diagnostic) > 500:
        diagnostic = diagnostic[:500] + "..."

    raise SnapshotError(
        f"{operation} failed with exit code "
        f"{result.exit_code}: {diagnostic}"
    )

def read_git_head(repository_path, git_executable="git"):
    """Read the exact HEAD commit of a Git repository."""

    repository_path = Path(repository_path).resolve()

    result = run_command(
        [
            git_executable,
            "rev-parse",
            "HEAD",
        ],
        repository_path,
    )

    require_success(
        result,
        "read Git HEAD",
    )

    try:
        commit = result.stdout.decode(
            "ascii",
            errors="strict",
        ).strip()
    except UnicodeDecodeError as exc:
        raise SnapshotError(
            "Git HEAD output is not ASCII"
        ) from exc

    if len(commit) != 40:
        raise SnapshotError(
            f"Git HEAD is not a full commit SHA: {commit}"
        )

    if any(
        character not in "0123456789abcdefABCDEF"
        for character in commit
    ):
        raise SnapshotError(
            f"Git HEAD is not hexadecimal: {commit}"
        )

    return commit.lower()


def clone_frozen_repository(
    spec,
    destination,
    git_executable="git",
):
    """Clone and verify one frozen repository commit."""

    destination = Path(destination).resolve()

    if destination.exists():
        raise SnapshotError(
            "repository destination already exists: "
            f"{destination}"
        )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    clone_result = run_command(
        [
            git_executable,
            "clone",
            "--no-checkout",
            spec.repository_url,
            str(destination),
        ],
        destination.parent,
    )

    require_success(
        clone_result,
        f"clone repository for {spec.case_id}",
    )

    checkout_result = run_command(
        [
            git_executable,
            "checkout",
            "--detach",
            spec.repository_commit,
        ],
        destination,
    )

    require_success(
        checkout_result,
        f"checkout frozen commit for {spec.case_id}",
    )

    checked_out_commit = read_git_head(
        destination,
        git_executable=git_executable,
    )

    requested_commit = (
        spec.repository_commit.lower()
    )

    if checked_out_commit != requested_commit:
        raise SnapshotError(
            "checked-out commit does not match "
            f"the frozen case: {spec.case_id}"
        )

    return RepositoryCheckout(
        repository_path=str(destination),
        requested_commit=requested_commit,
        checked_out_commit=checked_out_commit,
    )

def decode_utf8_strict(data, artifact_name):
    """Decode artifact bytes as strict UTF-8."""

    if not isinstance(data, bytes):
        raise SnapshotError(
            f"{artifact_name} must be bytes"
        )

    try:
        return data.decode(
            "utf-8",
            errors="strict",
        )
    except UnicodeDecodeError as exc:
        raise SnapshotError(
            f"{artifact_name} is not valid UTF-8"
        ) from exc


def run_why_blame(
    spec,
    repository_path,
    python_executable,
    main_path,
):
    """Run the evaluated Why-Blame product for one frozen case."""

    repository_path = Path(
        repository_path
    ).resolve()

    python_executable = Path(
        python_executable
    ).resolve()

    main_path = Path(main_path).resolve()

    if not repository_path.is_dir():
        raise SnapshotError(
            "repository path does not exist: "
            f"{repository_path}"
        )

    if not python_executable.is_file():
        raise SnapshotError(
            "Python executable does not exist: "
            f"{python_executable}"
        )

    if not main_path.is_file():
        raise SnapshotError(
            "evaluated main.py does not exist: "
            f"{main_path}"
        )

    target_path = (
        repository_path
        / spec.target_file
    ).resolve()

    try:
        target_path.relative_to(
            repository_path
        )
    except ValueError as exc:
        raise SnapshotError(
            f"target escapes repository: {spec.case_id}"
        ) from exc

    if not target_path.is_file():
        raise SnapshotError(
            f"target file does not exist: {spec.case_id}"
        )

    result = run_command(
        [
            str(python_executable),
            str(main_path),
            spec.target,
        ],
        repository_path,
        environment={
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
        },
    )

    require_success(
        result,
        f"Why-Blame analysis for {spec.case_id}",
    )

    decode_utf8_strict(
        result.stdout,
        "stdout",
    )

    decode_utf8_strict(
        result.stderr,
        "stderr",
    )

    return result


def write_case_artifacts(
    output_directory,
    spec,
    checkout,
    result,
    evaluated_product_commit,
    snapshot_runner_commit,
):
    """Write exact bytes, UTF-8 text, and metadata for one case."""

    output_directory = ensure_new_output_directory(
        output_directory
    )

    evaluated_product_commit = str(
        evaluated_product_commit
    ).lower()

    snapshot_runner_commit = str(
        snapshot_runner_commit
    ).lower()

    for name, commit in (
        (
            "evaluated_product_commit",
            evaluated_product_commit,
        ),
        (
            "snapshot_runner_commit",
            snapshot_runner_commit,
        ),
    ):
        if (
            len(commit) != 40
            or any(
                character
                not in "0123456789abcdef"
                for character in commit
            )
        ):
            raise SnapshotError(
                f"{name} must be a full commit SHA"
            )

    stdout_text = decode_utf8_strict(
        result.stdout,
        "stdout",
    )

    stderr_text = decode_utf8_strict(
        result.stderr,
        "stderr",
    )

    stdout_binary_path = (
        output_directory
        / "stdout.bin"
    )
    stderr_binary_path = (
        output_directory
        / "stderr.bin"
    )
    stdout_text_path = (
        output_directory
        / "stdout.txt"
    )
    stderr_text_path = (
        output_directory
        / "stderr.txt"
    )
    metadata_path = (
        output_directory
        / "metadata.json"
    )

    stdout_binary_path.write_bytes(
        result.stdout
    )

    stderr_binary_path.write_bytes(
        result.stderr
    )

    stdout_text_path.write_text(
        stdout_text,
        encoding="utf-8",
        newline="\n",
    )

    stderr_text_path.write_text(
        stderr_text,
        encoding="utf-8",
        newline="\n",
    )

    metadata = {
        "schema_version": 1,
        "evaluation_type": (
            "current_main_snapshot"
        ),
        "case_id": spec.case_id,
        "evaluated_product_commit": (
            evaluated_product_commit
        ),
        "snapshot_runner_commit": (
            snapshot_runner_commit
        ),
        "repository": {
            "url": spec.repository_url,
            "requested_commit": (
                checkout.requested_commit
            ),
            "checked_out_commit": (
                checkout.checked_out_commit
            ),
        },
        "target": {
            "file": spec.target_file,
            "start_line": spec.start_line,
            "end_line": spec.end_line,
            "argument": spec.target,
        },
        "execution": {
            "command": list(
                result.command
            ),
            "working_directory": (
                result.working_directory
            ),
            "started_at_utc": (
                result.started_at_utc
            ),
            "finished_at_utc": (
                result.finished_at_utc
            ),
            "exit_code": (
                result.exit_code
            ),
            "stdout_encoding": "utf-8",
            "stderr_encoding": "utf-8",
            "decode_errors": "strict",
            "python_version": (
                platform.python_version()
            ),
            "platform": (
                platform.platform()
            ),
        },
        "artifacts": {
            "stdout_binary_file": (
                "stdout.bin"
            ),
            "stderr_binary_file": (
                "stderr.bin"
            ),
            "stdout_text_file": (
                "stdout.txt"
            ),
            "stderr_text_file": (
                "stderr.txt"
            ),
            "stdout_bytes": len(
                result.stdout
            ),
            "stderr_bytes": len(
                result.stderr
            ),
            "stdout_sha256": (
                hashlib.sha256(
                    result.stdout
                ).hexdigest().upper()
            ),
            "stderr_sha256": (
                hashlib.sha256(
                    result.stderr
                ).hexdigest().upper()
            ),
        },
    }

    metadata_path.write_text(
        json.dumps(
            metadata,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    return metadata
