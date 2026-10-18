import json
from dataclasses import dataclass
from pathlib import Path

from .confidence import (
    VALID_CONFIDENCE_LEVELS,
    normalize_confidence,
)


VALID_CLAIM_STATUSES = {
    "PRESENTED",
    "ABSTAINED",
    "WITHHELD",
    "MISSED",
    "NOT_REACHED",
    "UNSAFE_PRESENTED",
    "NOT_APPLICABLE",
}


VALID_WITHHELD_REASONS = {
    "INSUFFICIENT_EVIDENCE",
    "CONFLICTING_EVIDENCE",
    "NOT_OBSERVED",
    "OUTSIDE_SUPPORTED_SCOPE",
}


class AnnotationError(ValueError):
    pass


@dataclass(frozen=True)
class ClaimAnnotation:
    status: str
    raw_evidence: str
    withheld_reason: str = ""


@dataclass(frozen=True)
class Annotation:
    schema_version: int
    case_id: str
    completed: bool
    failure_stage: str
    failure_type: str
    confidence_level: str
    confidence_source: str
    claims: dict[str, ClaimAnnotation]


def _require_nonempty_string(
    value,
    field_name,
):
    if (
        not isinstance(value, str)
        or not value.strip()
    ):
        raise AnnotationError(
            f"{field_name} must be a non-empty string"
        )

    return value.strip()


def _optional_string(
    value,
    field_name,
):
    if not isinstance(value, str):
        raise AnnotationError(
            f"{field_name} must be a string"
        )

    return value


def load_annotation(path: Path) -> Annotation:
    try:
        data = json.loads(
            path.read_text(
                encoding="utf-8-sig"
            )
        )
    except json.JSONDecodeError as exc:
        raise AnnotationError(
            f"{path.name}: invalid JSON"
        ) from exc

    if not isinstance(data, dict):
        raise AnnotationError(
            f"{path.name}: root must be an object"
        )

    schema_version = data.get(
        "schema_version"
    )

    if schema_version != 2:
        raise AnnotationError(
            f"{path.name}: schema_version must be 2"
        )

    case_id = _require_nonempty_string(
        data.get("case_id"),
        "case_id",
    )

    execution = data.get("execution")

    if not isinstance(execution, dict):
        raise AnnotationError(
            "execution must be an object"
        )

    completed = execution.get(
        "completed"
    )

    if not isinstance(completed, bool):
        raise AnnotationError(
            "execution.completed must be bool"
        )

    failure_stage = _optional_string(
        execution.get(
            "failure_stage",
            "",
        ),
        "execution.failure_stage",
    )

    failure_type = _optional_string(
        execution.get(
            "failure_type",
            "",
        ),
        "execution.failure_type",
    )

    confidence = data.get("confidence")

    if not isinstance(confidence, dict):
        raise AnnotationError(
            "confidence must be an object"
        )

    raw_level = confidence.get("level")
    confidence_level = (
        normalize_confidence(raw_level)
    )

    if (
        confidence_level == "UNKNOWN"
        and raw_level != "UNKNOWN"
    ):
        raise AnnotationError(
            "confidence.level is invalid"
        )

    if (
        confidence_level
        not in VALID_CONFIDENCE_LEVELS
    ):
        raise AnnotationError(
            "confidence.level is invalid"
        )

    confidence_source = (
        _require_nonempty_string(
            confidence.get("source"),
            "confidence.source",
        )
    )

    claims_data = data.get("claims")

    if not isinstance(claims_data, dict):
        raise AnnotationError(
            "claims must be an object"
        )

    claims = {}

    for claim_id, claim_data in (
        claims_data.items()
    ):
        claim_id = _require_nonempty_string(
            claim_id,
            "claim ID",
        )

        if not isinstance(
            claim_data,
            dict,
        ):
            raise AnnotationError(
                f"{claim_id} must be an object"
            )

        status = claim_data.get("status")

        if status not in VALID_CLAIM_STATUSES:
            raise AnnotationError(
                f"{claim_id}: invalid status"
            )

        raw_evidence = _optional_string(
            claim_data.get(
                "raw_evidence",
                "",
            ),
            f"{claim_id}.raw_evidence",
        )

        if "withheld_reason" in claim_data:
            withheld_reason = _require_nonempty_string(
                claim_data.get("withheld_reason"),
                f"{claim_id}.withheld_reason",
            )
        else:
            withheld_reason = ""

        if (
            withheld_reason
            and status != "WITHHELD"
        ):
            raise AnnotationError(
                f"{claim_id}: withheld_reason requires "
                "WITHHELD status"
            )

        if (
            withheld_reason
            and withheld_reason
            not in VALID_WITHHELD_REASONS
        ):
            raise AnnotationError(
                f"{claim_id}: invalid withheld_reason"
            )

        claims[claim_id] = ClaimAnnotation(
            status=status,
            raw_evidence=raw_evidence,
            withheld_reason=withheld_reason,
        )

    return Annotation(
        schema_version=schema_version,
        case_id=case_id,
        completed=completed,
        failure_stage=failure_stage,
        failure_type=failure_type,
        confidence_level=confidence_level,
        confidence_source=confidence_source,
        claims=claims,
    )
