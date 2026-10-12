"""Holdout v2 cross-reference validation."""


def validate_candidate_reference(
    cases,
    candidate,
):
    if candidate["case_id"] not in cases:
        raise ValueError(
            f"Unknown case_id: {candidate['case_id']}"
        )

    case = cases[candidate["case_id"]]

    if (
        case["repository"]
        != candidate["repository"]
    ):
        raise ValueError(
            "Repository mismatch"
        )

    if "claim_id" in candidate:
        claims = case.get("claims", [])

        if candidate["claim_id"] not in claims:
            raise ValueError(
                f"Unknown claim_id: {candidate['claim_id']}"
            )


def validate_candidate_set(
    candidates,
):
    seen = set()

    for candidate in candidates:
        candidate_id = candidate["candidate_id"]

        if candidate_id in seen:
            raise ValueError(
                f"Duplicate candidate_id: {candidate_id}"
            )

        seen.add(candidate_id)
