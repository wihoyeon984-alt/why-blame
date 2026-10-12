"""Holdout v2 cross-reference validation."""

from .validation import (
    validate_annotation_against_case,
)


class CrossReferenceError(ValueError):
    """Raised when Holdout v2 artifacts disagree."""


def validate_candidate_reference(
    candidate,
    case,
    annotation=None,
):
    if candidate.schema_version != case.schema_version:
        raise CrossReferenceError(
            "schema_version mismatch: "
            f"{candidate.schema_version!r} != "
            f"{case.schema_version!r}"
        )

    if candidate.candidate_id != case.case_id:
        raise CrossReferenceError(
            "candidate_id and case_id mismatch: "
            f"{candidate.candidate_id!r} != "
            f"{case.case_id!r}"
        )

    if candidate.repository.url != case.repository_url:
        raise CrossReferenceError(
            "repository URL mismatch: "
            f"{candidate.repository.url!r} != "
            f"{case.repository_url!r}"
        )

    if (
        candidate.repository.commit
        != case.repository_commit
    ):
        raise CrossReferenceError(
            "repository commit mismatch: "
            f"{candidate.repository.commit!r} != "
            f"{case.repository_commit!r}"
        )

    if annotation is not None:
        try:
            validate_annotation_against_case(
                case,
                annotation,
            )
        except ValueError as exc:
            raise CrossReferenceError(
                str(exc)
            ) from exc


def validate_candidate_set(
    candidates,
):
    seen = set()

    for candidate in candidates:
        candidate_id = candidate.candidate_id

        if candidate_id in seen:
            raise CrossReferenceError(
                "duplicate candidate_id: "
                f"{candidate_id}"
            )

        seen.add(candidate_id)
