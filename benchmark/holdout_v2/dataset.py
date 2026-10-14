"""End-to-end validation for Holdout v2 datasets."""

from dataclasses import dataclass
from pathlib import Path

from .loader import (
    LoadedCandidateArtifacts,
    load_candidate_artifacts,
)
from .validator import (
    validate_candidate_set,
)


class DatasetError(ValueError):
    """Raised when a Holdout v2 dataset is inconsistent."""


@dataclass(frozen=True)
class ValidatedDataset:
    """A fully validated Holdout v2 dataset."""

    artifacts: tuple[LoadedCandidateArtifacts, ...]


def _resolve_registered_path(
    holdout_dir,
    artifact_path,
    field_name,
):
    root = Path(holdout_dir).resolve()

    if (
        not isinstance(artifact_path, str)
        or not artifact_path.strip()
    ):
        raise DatasetError(
            f"{field_name} is required"
        )

    relative_path = Path(
        artifact_path
    )

    if relative_path.is_absolute():
        raise DatasetError(
            f"{field_name} must be relative"
        )

    resolved_path = (
        root / relative_path
    ).resolve()

    try:
        resolved_path.relative_to(root)
    except ValueError as exc:
        raise DatasetError(
            f"{field_name} escapes holdout directory"
        ) from exc

    if not resolved_path.is_file():
        raise DatasetError(
            f"{field_name} does not exist: "
            f"{artifact_path}"
        )

    return resolved_path


def _relative_key(
    holdout_dir,
    path,
):
    root = Path(holdout_dir).resolve()

    return path.resolve().relative_to(
        root
    ).as_posix()


def _find_json_artifacts(
    holdout_dir,
    directory_name,
):
    root = Path(holdout_dir).resolve()
    directory = root / directory_name

    if not directory.is_dir():
        return set()

    return {
        _relative_key(
            root,
            path,
        )
        for path in directory.rglob("*.json")
        if path.is_file()
    }


def _validate_no_orphans(
    holdout_dir,
    registered_paths,
):
    actual_paths = set()

    for directory_name in (
        "cases",
        "results",
        "annotations",
    ):
        actual_paths.update(
            _find_json_artifacts(
                holdout_dir,
                directory_name,
            )
        )

    orphan_paths = sorted(
        actual_paths - registered_paths
    )

    if orphan_paths:
        raise DatasetError(
            "orphan artifact: "
            + ", ".join(orphan_paths)
        )


def validate_dataset(
    candidates,
    holdout_dir,
):
    """Validate all registered Holdout v2 artifacts."""

    candidate_list = tuple(candidates)

    try:
        validate_candidate_set(
            candidate_list
        )
    except ValueError as exc:
        raise DatasetError(
            str(exc)
        ) from exc

    loaded_artifacts = []
    registered_paths = set()

    for candidate in candidate_list:
        try:
            loaded = load_candidate_artifacts(
                candidate,
                holdout_dir,
            )
        except ValueError as exc:
            raise DatasetError(
                str(exc)
            ) from exc

        loaded_artifacts.append(
            loaded
        )

        registered_paths.add(
            _relative_key(
                holdout_dir,
                _resolve_registered_path(
                    holdout_dir,
                    candidate.artifacts.case_file,
                    "artifacts.case_file",
                ),
            )
        )

        result_file = (
            candidate.artifacts.result_file
        )

        if result_file:
            registered_paths.add(
                _relative_key(
                    holdout_dir,
                    _resolve_registered_path(
                        holdout_dir,
                        result_file,
                        "artifacts.result_file",
                    ),
                )
            )

        annotation_file = (
            candidate.artifacts.annotation_file
        )

        if annotation_file:
            registered_paths.add(
                _relative_key(
                    holdout_dir,
                    _resolve_registered_path(
                        holdout_dir,
                        annotation_file,
                        "artifacts.annotation_file",
                    ),
                )
            )

    _validate_no_orphans(
        holdout_dir,
        registered_paths,
    )

    return ValidatedDataset(
        artifacts=tuple(
            loaded_artifacts
        ),
    )
