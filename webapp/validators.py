import subprocess
from dataclasses import dataclass
from pathlib import Path


class ValidationError(ValueError):
    """Raised when dashboard input is unsafe or invalid."""


@dataclass(frozen=True)
class ValidatedTarget:
    repository: Path
    relative_file: str
    start_line: int
    end_line: int


def is_git_repository(repository):
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repository),
                "rev-parse",
                "--is-inside-work-tree",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError:
        return False

    return (
        result.returncode == 0
        and result.stdout.strip().lower() == "true"
    )


def validate_target(
    repository_path,
    file_path,
    start_line,
    end_line,
):
    repository = Path(repository_path).expanduser().resolve()

    if not repository.is_dir():
        raise ValidationError(
            "The repository path must be an existing directory."
        )

    if not is_git_repository(repository):
        raise ValidationError(
            "The repository path must be a Git work tree."
        )

    raw_file = str(file_path).strip()

    if not raw_file:
        raise ValidationError(
            "The file path is required."
        )

    requested_file = Path(raw_file)

    if requested_file.is_absolute():
        raise ValidationError(
            "The file path must be relative to the repository."
        )

    resolved_file = (
        repository
        / requested_file
    ).resolve()

    try:
        relative_file = resolved_file.relative_to(
            repository
        )
    except ValueError as exc:
        raise ValidationError(
            "The file path must stay inside the repository."
        ) from exc

    if not resolved_file.is_file():
        raise ValidationError(
            "The requested file does not exist."
        )

    if isinstance(start_line, bool) or not isinstance(
        start_line,
        int,
    ):
        raise ValidationError(
            "The start line must be an integer."
        )

    if isinstance(end_line, bool) or not isinstance(
        end_line,
        int,
    ):
        raise ValidationError(
            "The end line must be an integer."
        )

    if start_line < 1 or end_line < 1:
        raise ValidationError(
            "Line numbers must be at least 1."
        )

    if start_line > end_line:
        raise ValidationError(
            "The start line cannot exceed the end line."
        )

    return ValidatedTarget(
        repository=repository,
        relative_file=relative_file.as_posix(),
        start_line=start_line,
        end_line=end_line,
    )
