"""Safely capture a Holdout v2 current-main evaluation snapshot."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path


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
