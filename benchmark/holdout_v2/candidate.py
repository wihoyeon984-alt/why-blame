import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath


VALID_CANDIDATE_STATUSES = {
    "PROPOSED",
    "ELIGIBLE",
    "EXCLUDED",
    "FROZEN",
    "EXECUTED",
    "ANNOTATED",
}

VALID_EXCLUSION_CODES = {
    "",
    "DUPLICATES_V1",
    "DUPLICATES_V2",
    "REPOSITORY_UNAVAILABLE",
    "COMMIT_UNAVAILABLE",
    "TARGET_NOT_FOUND",
    "HISTORY_UNAVAILABLE",
    "PRIVATE_EVIDENCE_REQUIRED",
    "GROUND_TRUTH_UNRESOLVABLE",
    "LEGAL_RESTRICTION",
    "OTHER",
}

CANDIDATE_ID_PATTERN = re.compile(
    r"^[a-z0-9]+(?:_[a-z0-9]+)*$"
)

COMMIT_PATTERN = re.compile(
    r"^[0-9a-f]{40}$"
)


class CandidateError(ValueError):
    pass


@dataclass(frozen=True)
class RepositoryReference:
    url: str
    commit: str


@dataclass(frozen=True)
class TargetReference:
    file: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class CandidateSelection:
    rationale: str
    proposed_at: str
    proposed_by: str


@dataclass(frozen=True)
class CandidateExclusion:
    code: str
    reason: str


@dataclass(frozen=True)
class CandidateIntegrity:
    overlaps_holdout_v1: bool
    overlap_details: str
    ground_truth_frozen: bool
    system_executed: bool
    annotation_complete: bool


@dataclass(frozen=True)
class CandidateArtifacts:
    case_file: str
    result_file: str
    annotation_file: str


@dataclass(frozen=True)
class Candidate:
    schema_version: int
    candidate_id: str
    repository: RepositoryReference
    target: TargetReference
    status: str
    selection: CandidateSelection
    exclusion: CandidateExclusion
    integrity: CandidateIntegrity
    artifacts: CandidateArtifacts
    notes: str


def _require_object(value, field_name):
    if not isinstance(value, dict):
        raise CandidateError(
            f"{field_name} must be an object"
        )

    return value


def _require_string(
    value,
    field_name,
    allow_empty=False,
):
    if not isinstance(value, str):
        raise CandidateError(
            f"{field_name} must be a string"
        )

    value = value.strip()

    if not allow_empty and not value:
        raise CandidateError(
            f"{field_name} must not be empty"
        )

    return value


def _require_bool(value, field_name):
    if not isinstance(value, bool):
        raise CandidateError(
            f"{field_name} must be bool"
        )

    return value


def _validate_target_path(value):
    value = _require_string(
        value,
        "target.file",
    )

    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)

    if path.is_absolute():
        raise CandidateError(
            "target.file must be relative"
        )

    if ".." in path.parts:
        raise CandidateError(
            "target.file must not contain '..'"
        )

    return normalized


def _validate_date(value):
    value = _require_string(
        value,
        "selection.proposed_at",
    )

    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise CandidateError(
            "selection.proposed_at must use "
            "YYYY-MM-DD"
        ) from exc

    return value


def _require_artifact(
    artifacts,
    field_name,
):
    if not getattr(artifacts, field_name):
        raise CandidateError(
            f"artifacts.{field_name} is required"
        )


def _validate_state(candidate):
    status = candidate.status
    integrity = candidate.integrity
    artifacts = candidate.artifacts
    exclusion = candidate.exclusion

    if status == "EXCLUDED":
        if not exclusion.code:
            raise CandidateError(
                "excluded candidate requires "
                "exclusion.code"
            )

        if not exclusion.reason:
            raise CandidateError(
                "excluded candidate requires "
                "exclusion.reason"
            )
    elif exclusion.code or exclusion.reason:
        raise CandidateError(
            "non-excluded candidate must not "
            "contain exclusion details"
        )

    if status in {
        "PROPOSED",
        "ELIGIBLE",
        "EXCLUDED",
    }:
        if integrity.ground_truth_frozen:
            raise CandidateError(
                f"{status} candidate must not "
                "have frozen Ground Truth"
            )

        if integrity.system_executed:
            raise CandidateError(
                f"{status} candidate must not "
                "be executed"
            )

        if integrity.annotation_complete:
            raise CandidateError(
                f"{status} candidate must not "
                "be annotated"
            )

    if status == "FROZEN":
        if not integrity.ground_truth_frozen:
            raise CandidateError(
                "FROZEN candidate requires "
                "frozen Ground Truth"
            )

        if integrity.system_executed:
            raise CandidateError(
                "FROZEN candidate must not "
                "already be executed"
            )

        if integrity.annotation_complete:
            raise CandidateError(
                "FROZEN candidate must not "
                "already be annotated"
            )

        _require_artifact(
            artifacts,
            "case_file",
        )

    if status == "EXECUTED":
        if not integrity.ground_truth_frozen:
            raise CandidateError(
                "EXECUTED candidate requires "
                "frozen Ground Truth"
            )

        if not integrity.system_executed:
            raise CandidateError(
                "EXECUTED candidate requires "
                "system_executed=true"
            )

        if integrity.annotation_complete:
            raise CandidateError(
                "EXECUTED candidate must not "
                "already be annotated"
            )

        _require_artifact(
            artifacts,
            "case_file",
        )
        _require_artifact(
            artifacts,
            "result_file",
        )

    if status == "ANNOTATED":
        if not integrity.ground_truth_frozen:
            raise CandidateError(
                "ANNOTATED candidate requires "
                "frozen Ground Truth"
            )

        if not integrity.system_executed:
            raise CandidateError(
                "ANNOTATED candidate requires "
                "system_executed=true"
            )

        if not integrity.annotation_complete:
            raise CandidateError(
                "ANNOTATED candidate requires "
                "annotation_complete=true"
            )

        _require_artifact(
            artifacts,
            "case_file",
        )
        _require_artifact(
            artifacts,
            "result_file",
        )
        _require_artifact(
            artifacts,
            "annotation_file",
        )

    if (
        status != "EXCLUDED"
        and integrity.overlaps_holdout_v1
    ):
        raise CandidateError(
            "candidate overlapping Holdout v1 "
            "must be excluded"
        )


def load_candidate(path: Path) -> Candidate:
    try:
        data = json.loads(
            path.read_text(
                encoding="utf-8-sig"
            )
        )
    except json.JSONDecodeError as exc:
        raise CandidateError(
            f"{path.name}: invalid JSON"
        ) from exc

    data = _require_object(data, "root")

    if data.get("schema_version") != 2:
        raise CandidateError(
            "schema_version must be 2"
        )

    candidate_id = _require_string(
        data.get("candidate_id"),
        "candidate_id",
    )

    if not CANDIDATE_ID_PATTERN.fullmatch(
        candidate_id
    ):
        raise CandidateError(
            "candidate_id has invalid format"
        )

    repository_data = _require_object(
        data.get("repository"),
        "repository",
    )

    repository_url = _require_string(
        repository_data.get("url"),
        "repository.url",
    )

    if not repository_url.startswith(
        "https://"
    ):
        raise CandidateError(
            "repository.url must use https"
        )

    repository_commit = _require_string(
        repository_data.get("commit"),
        "repository.commit",
    ).lower()

    if not COMMIT_PATTERN.fullmatch(
        repository_commit
    ):
        raise CandidateError(
            "repository.commit must be a "
            "40-character hexadecimal SHA"
        )

    target_data = _require_object(
        data.get("target"),
        "target",
    )

    target_file = _validate_target_path(
        target_data.get("file")
    )

    start_line = target_data.get(
        "start_line"
    )
    end_line = target_data.get(
        "end_line"
    )

    if (
        not isinstance(start_line, int)
        or isinstance(start_line, bool)
        or start_line < 1
    ):
        raise CandidateError(
            "target.start_line must be "
            "a positive integer"
        )

    if (
        not isinstance(end_line, int)
        or isinstance(end_line, bool)
        or end_line < start_line
    ):
        raise CandidateError(
            "target.end_line must not be "
            "less than start_line"
        )

    if end_line - start_line + 1 > 200:
        raise CandidateError(
            "target range must not exceed "
            "200 lines"
        )

    status = _require_string(
        data.get("status"),
        "status",
    )

    if status not in VALID_CANDIDATE_STATUSES:
        raise CandidateError(
            "status is invalid"
        )

    selection_data = _require_object(
        data.get("selection"),
        "selection",
    )

    selection = CandidateSelection(
        rationale=_require_string(
            selection_data.get("rationale"),
            "selection.rationale",
        ),
        proposed_at=_validate_date(
            selection_data.get("proposed_at")
        ),
        proposed_by=_require_string(
            selection_data.get("proposed_by"),
            "selection.proposed_by",
        ),
    )

    exclusion_data = _require_object(
        data.get("exclusion"),
        "exclusion",
    )

    exclusion_code = _require_string(
        exclusion_data.get("code", ""),
        "exclusion.code",
        allow_empty=True,
    )

    if exclusion_code not in (
        VALID_EXCLUSION_CODES
    ):
        raise CandidateError(
            "exclusion.code is invalid"
        )

    exclusion = CandidateExclusion(
        code=exclusion_code,
        reason=_require_string(
            exclusion_data.get("reason", ""),
            "exclusion.reason",
            allow_empty=True,
        ),
    )

    integrity_data = _require_object(
        data.get("integrity"),
        "integrity",
    )

    integrity = CandidateIntegrity(
        overlaps_holdout_v1=_require_bool(
            integrity_data.get(
                "overlaps_holdout_v1"
            ),
            "integrity.overlaps_holdout_v1",
        ),
        overlap_details=_require_string(
            integrity_data.get(
                "overlap_details",
                "",
            ),
            "integrity.overlap_details",
            allow_empty=True,
        ),
        ground_truth_frozen=_require_bool(
            integrity_data.get(
                "ground_truth_frozen"
            ),
            "integrity.ground_truth_frozen",
        ),
        system_executed=_require_bool(
            integrity_data.get(
                "system_executed"
            ),
            "integrity.system_executed",
        ),
        annotation_complete=_require_bool(
            integrity_data.get(
                "annotation_complete"
            ),
            "integrity.annotation_complete",
        ),
    )

    artifacts_data = _require_object(
        data.get("artifacts"),
        "artifacts",
    )

    artifacts = CandidateArtifacts(
        case_file=_require_string(
            artifacts_data.get(
                "case_file",
                "",
            ),
            "artifacts.case_file",
            allow_empty=True,
        ),
        result_file=_require_string(
            artifacts_data.get(
                "result_file",
                "",
            ),
            "artifacts.result_file",
            allow_empty=True,
        ),
        annotation_file=_require_string(
            artifacts_data.get(
                "annotation_file",
                "",
            ),
            "artifacts.annotation_file",
            allow_empty=True,
        ),
    )

    candidate = Candidate(
        schema_version=2,
        candidate_id=candidate_id,
        repository=RepositoryReference(
            url=repository_url,
            commit=repository_commit,
        ),
        target=TargetReference(
            file=target_file,
            start_line=start_line,
            end_line=end_line,
        ),
        status=status,
        selection=selection,
        exclusion=exclusion,
        integrity=integrity,
        artifacts=artifacts,
        notes=_require_string(
            data.get("notes", ""),
            "notes",
            allow_empty=True,
        ),
    )

    _validate_state(candidate)

    return candidate
