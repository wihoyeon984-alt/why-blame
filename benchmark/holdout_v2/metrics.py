from .validation import (
    validate_annotation_against_case,
)


PRESENTATION_STATUSES = {
    "PRESENTED",
    "UNSAFE_PRESENTED",
}


def safe_divide(
    numerator,
    denominator,
):
    if denominator == 0:
        return None

    return numerator / denominator


def _empty_group():
    return {
        "case_count": 0,
        "supported_total": 0,
        "supported_presented": 0,
        "total_presentations": 0,
        "unsafe_presented": 0,
    }


def _finalize_group(group):
    result = dict(group)

    result["claim_precision"] = safe_divide(
        group["supported_presented"],
        group["total_presentations"],
    )

    result["supported_recall"] = safe_divide(
        group["supported_presented"],
        group["supported_total"],
    )

    result[
        "unsafe_presentation_rate"
    ] = safe_divide(
        group["unsafe_presented"],
        group["total_presentations"],
    )

    return result


def compute_confidence_metrics(
    cases,
    annotations,
):
    groups = {}

    for case in cases:
        annotation = annotations.get(
            case.case_id
        )

        if annotation is None:
            raise ValueError(
                "missing annotation for case: "
                f"{case.case_id}"
            )

        validate_annotation_against_case(
            case,
            annotation,
        )

        level = annotation.confidence_level

        group = groups.setdefault(
            level,
            _empty_group(),
        )

        group["case_count"] += 1

        for claim_id, claim in (
            case.claims.items()
        ):
            claim_annotation = (
                annotation.claims[claim_id]
            )

            status = claim_annotation.status

            if claim.label == "SUPPORTED":
                group["supported_total"] += 1

                if status == "PRESENTED":
                    group[
                        "supported_presented"
                    ] += 1

            if status in PRESENTATION_STATUSES:
                group[
                    "total_presentations"
                ] += 1

            if status == "UNSAFE_PRESENTED":
                group[
                    "unsafe_presented"
                ] += 1

    return {
        level: _finalize_group(group)
        for level, group in sorted(
            groups.items()
        )
    }
