import json
from dataclasses import dataclass
from pathlib import Path


VALID_CLAIM_LABELS = {
    "SUPPORTED",
    "UNSUPPORTED",
    "AMBIGUOUS",
    "CONFLICTING",
}


class CaseError(ValueError):
    pass


@dataclass(frozen=True)
class GroundTruthClaim:
    claim_id: str
    label: str


@dataclass(frozen=True)
class HoldoutCase:
    schema_version: int
    case_id: str
    repository_url: str
    repository_commit: str
    frozen: bool
    claims: dict[str, GroundTruthClaim]


def _require_nonempty_string(
    value,
    field_name,
):
    if (
        not isinstance(value, str)
        or not value.strip()
    ):
        raise CaseError(
            f"{field_name} must be a non-empty string"
        )

    return value.strip()


def load_case(path: Path) -> HoldoutCase:
    try:
        data = json.loads(
            path.read_text(
                encoding="utf-8-sig"
            )
        )
    except json.JSONDecodeError as exc:
        raise CaseError(
            f"{path.name}: invalid JSON"
        ) from exc

    if not isinstance(data, dict):
        raise CaseError(
            f"{path.name}: root must be an object"
        )

    schema_version = data.get(
        "schema_version"
    )

    if schema_version != 2:
        raise CaseError(
            f"{path.name}: schema_version must be 2"
        )

    case_id = _require_nonempty_string(
        data.get("case_id"),
        "case_id",
    )

    repository = data.get("repository")

    if not isinstance(repository, dict):
        raise CaseError(
            "repository must be an object"
        )

    repository_url = _require_nonempty_string(
        repository.get("url"),
        "repository.url",
    )

    repository_commit = (
        _require_nonempty_string(
            repository.get("commit"),
            "repository.commit",
        )
    )

    frozen = data.get("frozen")

    if frozen is not True:
        raise CaseError(
            "frozen must be true"
        )

    claims_data = data.get("claims")

    if not isinstance(claims_data, dict):
        raise CaseError(
            "claims must be an object"
        )

    if not claims_data:
        raise CaseError(
            "claims must not be empty"
        )

    claims = {}

    for raw_claim_id, claim_data in (
        claims_data.items()
    ):
        claim_id = _require_nonempty_string(
            raw_claim_id,
            "claim ID",
        )

        if claim_id in claims:
            raise CaseError(
                f"duplicate claim ID: {claim_id}"
            )

        if not isinstance(claim_data, dict):
            raise CaseError(
                f"{claim_id} must be an object"
            )

        label = claim_data.get("label")

        if label not in VALID_CLAIM_LABELS:
            raise CaseError(
                f"{claim_id}: invalid label"
            )

        claims[claim_id] = GroundTruthClaim(
            claim_id=claim_id,
            label=label,
        )

    return HoldoutCase(
        schema_version=schema_version,
        case_id=case_id,
        repository_url=repository_url,
        repository_commit=repository_commit,
        frozen=frozen,
        claims=claims,
    )
