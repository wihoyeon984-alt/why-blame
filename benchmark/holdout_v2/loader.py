"""Load and validate Holdout v2 candidate artifacts."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .annotation import (
    Annotation,
    load_annotation,
)
from .case import (
    HoldoutCase,
    load_case,
)
from .validator import (
    validate_candidate_reference,
)


class LoaderError(ValueError):
    """Raised when candidate artifacts cannot be loaded safely."""


@dataclass(frozen=True)
class LoadedCandidateArtifacts:
    candidate: object
    case: HoldoutCase
    annotation: Optional[Annotation]


def _resolve_artifact_path(
    holdout_dir,
    artifact_path,
    field_name,
):
    root = Path(holdout_dir).resolve()
    relative_path = Path(artifact_path)

    if not artifact_path:
        raise LoaderError(
            f"{field_name} is required"
        )

    if relative_path.is_absolute():
        raise LoaderError(
            f"{field_name} must be relative"
        )

    resolved_path = (
        root / relative_path
    ).resolve()

    try:
        resolved_path.relative_to(root)
    except ValueError as exc:
        raise LoaderError(
            f"{field_name} escapes holdout directory"
        ) from exc

    if not resolved_path.is_file():
        raise LoaderError(
            f"{field_name} does not exist: "
            f"{artifact_path}"
        )

    return resolved_path


def load_candidate_artifacts(
    candidate,
    holdout_dir,
):
    case_path = _resolve_artifact_path(
        holdout_dir,
        candidate.artifacts.case_file,
        "artifacts.case_file",
    )

    case = load_case(
        case_path
    )

    annotation = None

    if candidate.artifacts.annotation_file:
        annotation_path = _resolve_artifact_path(
            holdout_dir,
            candidate.artifacts.annotation_file,
            "artifacts.annotation_file",
        )

        annotation = load_annotation(
            annotation_path
        )

    validate_candidate_reference(
        candidate,
        case,
        annotation,
    )

    return LoadedCandidateArtifacts(
        candidate=candidate,
        case=case,
        annotation=annotation,
    )
