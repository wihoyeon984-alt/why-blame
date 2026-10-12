class ValidationError(ValueError):
    pass


def validate_annotation_against_case(
    case,
    annotation,
):
    if case.schema_version != annotation.schema_version:
        raise ValidationError(
            "schema_version mismatch: "
            f"{case.schema_version!r} != "
            f"{annotation.schema_version!r}"
        )

    if case.case_id != annotation.case_id:
        raise ValidationError(
            "case_id mismatch: "
            f"{case.case_id!r} != "
            f"{annotation.case_id!r}"
        )

    case_claim_ids = set(case.claims)
    annotation_claim_ids = set(
        annotation.claims
    )

    missing_claim_ids = sorted(
        case_claim_ids
        - annotation_claim_ids
    )

    if missing_claim_ids:
        raise ValidationError(
            "missing claim annotations: "
            + ", ".join(missing_claim_ids)
        )

    unknown_claim_ids = sorted(
        annotation_claim_ids
        - case_claim_ids
    )

    if unknown_claim_ids:
        raise ValidationError(
            "unknown claim annotations: "
            + ", ".join(unknown_claim_ids)
        )
