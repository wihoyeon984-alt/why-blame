from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


VALID_LABELS = {
    "SUPPORTED",
    "UNSUPPORTED",
    "AMBIGUOUS",
    "CONFLICTING",
}

VALID_EXPOSURE_STATUSES = {
    "PRESENTED",
    "ABSTAINED",
    "NOT_REACHED",
    "UNSAFE_PRESENTED",
    "NOT_APPLICABLE",
}

OBSERVABLE_STATUSES = {
    "PRESENTED",
    "ABSTAINED",
    "UNSAFE_PRESENTED",
}

DEFAULT_IMPLEMENTATION_COMMIT = "2c4bf34"
DEFAULT_GROUND_TRUTH_COMMIT = "1b4f5f3"
DEFAULT_FIRST_RUN_COMMIT = "3a37a47"


@dataclass(frozen=True)
class GroundTruthClaim:
    claim_id: str
    label: str


@dataclass(frozen=True)
class HoldoutCase:
    case_id: str
    path: Path
    frozen: bool
    frozen_before_system_run: bool
    implementation_commit: str
    claims: tuple[GroundTruthClaim, ...]
    required_abstentions: int


@dataclass(frozen=True)
class ClaimAnnotation:
    status: str
    raw_evidence: str


@dataclass(frozen=True)
class CaseAnnotation:
    case_id: str
    completed: bool
    failure_stage: str
    failure_type: str
    claims: dict[str, ClaimAnnotation]


class ScoringError(ValueError):
    pass


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()

    if normalized == "true":
        return True

    if normalized == "false":
        return False

    raise ScoringError(
        f"invalid boolean value: {value!r}"
    )


def _find_scalar(text: str, key: str) -> str:
    pattern = re.compile(
        rf"(?m)^\s*{re.escape(key)}:"
        rf"\s*[\"']?([^\"'\r\n]+?)[\"']?\s*$"
    )

    match = pattern.search(text)

    if not match:
        raise ScoringError(
            f"missing scalar field: {key}"
        )

    return match.group(1).strip()


def _find_bool(text: str, key: str) -> bool:
    return _parse_bool(
        _find_scalar(text, key)
    )


def parse_case_file(path: Path) -> HoldoutCase:
    text = path.read_text(
        encoding="utf-8-sig"
    )

    case_id = _find_scalar(
        text,
        "id",
    )

    frozen = _find_bool(
        text,
        "frozen",
    )

    frozen_before_system_run = _find_bool(
        text,
        "frozen_before_system_run",
    )

    implementation_commit = _find_scalar(
        text,
        "implementation_commit",
    )

    claim_pattern = re.compile(
        r"(?ms)^\s{4}- id:\s*(claim_\d+)\s*$"
        r"(.*?)"
        r"(?=^\s{4}- id:\s*claim_\d+\s*$"
        r"|^system_run:)"
    )

    claims: list[GroundTruthClaim] = []

    for match in claim_pattern.finditer(text):
        claim_id = match.group(1)
        block = match.group(2)

        label_match = re.search(
            r"(?m)^\s{6}label:\s*(\w+)\s*$",
            block,
        )

        if not label_match:
            raise ScoringError(
                f"{path.name}: missing label "
                f"for {claim_id}"
            )

        label = label_match.group(1)

        if label not in VALID_LABELS:
            raise ScoringError(
                f"{path.name}: invalid label "
                f"{label!r} for {claim_id}"
            )

        claims.append(
            GroundTruthClaim(
                claim_id=claim_id,
                label=label,
            )
        )

    if not claims:
        raise ScoringError(
            f"{path.name}: "
            "no Ground Truth claims found"
        )

    claim_ids = [
        claim.claim_id
        for claim in claims
    ]

    if len(claim_ids) != len(set(claim_ids)):
        raise ScoringError(
            f"{path.name}: "
            "duplicate Ground Truth claim ID"
        )

    required_abstentions = int(
        _find_scalar(
            text,
            "required_abstentions",
        )
    )

    expected_required_abstentions = sum(
        claim.label
        in {
            "UNSUPPORTED",
            "AMBIGUOUS",
            "CONFLICTING",
        }
        for claim in claims
    )

    if (
        required_abstentions
        != expected_required_abstentions
    ):
        raise ScoringError(
            f"{path.name}: "
            f"required_abstentions="
            f"{required_abstentions}, "
            f"expected "
            f"{expected_required_abstentions}"
        )

    return HoldoutCase(
        case_id=case_id,
        path=path,
        frozen=frozen,
        frozen_before_system_run=(
            frozen_before_system_run
        ),
        implementation_commit=(
            implementation_commit
        ),
        claims=tuple(claims),
        required_abstentions=(
            required_abstentions
        ),
    )

def discover_cases(cases_dir: Path) -> list[aths = sorted(
        path
        for path in cases_dir.glob("*.yaml")
        if path.name != "CASE_TEMPLATE.yaml"
    )

    cases = [parse_case_file(path) for path in paths]

    case_ids = [case.case_id for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ScoringError("duplicate Holdout case ID")

    return cases

def discover_results(
    results_dir: Path,
) -> dict[str, Path]:
    results: dict[str, Path] = {}

    for path in sorted(
        results_dir.glob("*.txt")
    ):
        case_id = path.stem

        if case_id in results:
            raise ScoringError(
                f"duplicate result for case "
                f"{case_id}"
            )

        results[case_id] = path

    return results


def load_annotation(
    path: Path,
) -> CaseAnnotation:
    try:
        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except json.JSONDecodeError as exc:
        raise ScoringError(
            f"{path.name}: invalid JSON"
        ) from exc

    case_id = data.get("case_id")

    if (
        not isinstance(case_id, str)
        or not case_id
    ):
        raise ScoringError(
            f"{path.name}: invalid case_id"
        )

    execution = data.get("execution")

    if not isinstance(execution, dict):
        raise ScoringError(
            f"{path.name}: missing execution"
        )

    completed = execution.get(
        "completed"
    )

    if not isinstance(completed, bool):
        raise ScoringError(
            f"{path.name}: "
            "execution.completed must be bool"
        )

    failure_stage = execution.get(
        "failure_stage",
        "",
    )

    failure_type = execution.get(
        "failure_type",
        "",
    )

    claims_data = data.get("claims")

    if not isinstance(claims_data, dict):
        raise ScoringError(
            f"{path.name}: "
            "claims must be an object"
        )

    claims: dict[
        str,
        ClaimAnnotation,
    ] = {}

    for claim_id, value in claims_data.items():
        if not isinstance(value, dict):
            raise ScoringError(
                f"{path.name}: annotation for "
                f"{claim_id} must be an object"
            )

        status = value.get("status")

        if status not in VALID_EXPOSURE_STATUSES:
            raise ScoringError(
                f"{path.name}: invalid status "
                f"{status!r} for {claim_id}"
            )

        raw_evidence = value.get(
            "raw_evidence",
            "",
        )

        if not isinstance(
            raw_evidence,
            str,
        ):
            raise ScoringError(
                f"{path.name}: raw_evidence "
                f"for {claim_id} "
                "must be a string"
            )

        claims[claim_id] = ClaimAnnotation(
            status=status,
            raw_evidence=raw_evidence,
        )

    return CaseAnnotation(
        case_id=case_id,
        completed=completed,
        failure_stage=str(
            failure_stage
        ),
        failure_type=str(
            failure_type
        ),
        claims=claims,
    )


def discover_annotations(
    scoring_dir: Path,
) -> dict[str, CaseAnnotation]:
    annotations: dict[
        str,
        CaseAnnotation,
    ] = {}

    if not scoring_dir.exists():
        return annotations

    for path in sorted(
        scoring_dir.glob("*.json")
    ):
        annotation = load_annotation(
            path
        )

        if annotation.case_id in annotations:
            raise ScoringError(
                "duplicate annotation for "
                f"{annotation.case_id}"
            )

        annotations[
            annotation.case_id
        ] = annotation

    return annotations


def validate_benchmark(
    cases: Iterable[HoldoutCase],
    results: dict[str, Path],
    annotations: dict[
        str,
        CaseAnnotation,
    ],
    expected_implementation_commit: str,
) -> None:
    cases = list(cases)

    case_by_id = {
        case.case_id: case
        for case in cases
    }

    for case in cases:
        if not case.frozen:
            raise ScoringError(
                f"{case.case_id}: "
                "Ground Truth is not frozen"
            )

        if not case.frozen_before_system_run:
            raise ScoringError(
                f"{case.case_id}: "
                "Ground Truth was not frozen "
                "before system run"
            )

        if (
            case.implementation_commit
            != expected_implementation_commit
        ):
            raise ScoringError(
                f"{case.case_id}: "
                "implementation commit "
                f"{case.implementation_commit!r}, "
                "expected "
                f"{expected_implementation_commit!r}"
            )

        if case.case_id not in results:
            raise ScoringError(
                f"{case.case_id}: "
                "missing first-run result"
            )

    unknown_results = (
        set(results)
        - set(case_by_id)
    )

    if unknown_results:
        raise ScoringError(
            "results exist for unknown cases: "
            + ", ".join(
                sorted(unknown_results)
            )
        )

    unknown_annotations = (
        set(annotations)
        - set(case_by_id)
    )

    if unknown_annotations:
        raise ScoringError(
            "annotations exist for "
            "unknown cases: "
            + ", ".join(
                sorted(unknown_annotations)
            )
        )

    for (
        case_id,
        annotation,
    ) in annotations.items():
        case = case_by_id[case_id]

        valid_claim_ids = {
            claim.claim_id
            for claim in case.claims
        }

        unknown_claim_ids = (
            set(annotation.claims)
            - valid_claim_ids
        )

        if unknown_claim_ids:
            raise ScoringError(
                f"{case_id}: annotations "
                "contain unknown claim IDs: "
                + ", ".join(
                    sorted(
                        unknown_claim_ids
                    )
                )
            )


def summarize_ground_truth(
    cases: Iterable[HoldoutCase],
) -> dict[str, int]:
    cases = list(cases)

    labels = Counter(
        claim.label
        for case in cases
        for claim in case.claims
    )

    return {
        "cases": len(cases),
        "total_claims": sum(
            labels.values()
        ),
        "supported": labels[
            "SUPPORTED"
        ],
        "unsupported": labels[
            "UNSUPPORTED"
        ],
        "ambiguous": labels[
            "AMBIGUOUS"
        ],
        "conflicting": labels[
            "CONFLICTING"
        ],
        "required_abstentions": sum(
            case.required_abstentions
            for case in cases
        ),
    }


def summarize_exposure(
    cases: Iterable[HoldoutCase],
    annotations: dict[
        str,
        CaseAnnotation,
    ],
) -> dict[str, int]:
    statuses = Counter()

    for case in cases:
        annotation = annotations.get(
            case.case_id
        )

        if annotation is None:
            statuses[
                "UNANNOTATED"
            ] += len(case.claims)
            continue

        for claim in case.claims:
            claim_annotation = (
                annotation.claims.get(
                    claim.claim_id
                )
            )

            if claim_annotation is None:
                statuses[
                    "UNANNOTATED"
                ] += 1
                continue

            statuses[
                claim_annotation.status
            ] += 1

    return dict(statuses)


def safe_divide(
    numerator: int,
    denominator: int,
) -> float | None:
    if denominator == 0:
        return None

    return numerator / denominator


def compute_metrics(
    cases: Iterable[HoldoutCase],
    annotations: dict[
        str,
        CaseAnnotation,
    ],
) -> dict[
    str,
    float | int | bool | None,
]:
    cases = list(cases)

    total_cases = len(cases)

    completed_cases = sum(
        annotation.completed
        for annotation in annotations.values()
    )

    total_claims = 0
    supported_total = 0
    annotated_claims = 0
    supported_presented = 0
    observable_supported = 0
    not_reached = 0
    unsafe_presented = 0
    system_abstentions = 0
    correct_abstentions = 0
    required_abstentions = 0

    for case in cases:
        annotation = annotations.get(
            case.case_id
        )

        for claim in case.claims:
            total_claims += 1

            if claim.label == "SUPPORTED":
                supported_total += 1
            else:
                required_abstentions += 1

            if annotation is None:
                continue

            claim_annotation = (
                annotation.claims.get(
                    claim.claim_id
                )
            )

            if claim_annotation is None:
                continue

            annotated_claims += 1

            status = claim_annotation.status

            if status == "NOT_REACHED":
                not_reached += 1

            if status == "UNSAFE_PRESENTED":
                unsafe_presented += 1

            if (
                claim.label == "SUPPORTED"
                and status
                in OBSERVABLE_STATUSES
            ):
                observable_supported += 1

            if (
                claim.label == "SUPPORTED"
                and status == "PRESENTED"
            ):
                supported_presented += 1

            if status == "ABSTAINED":
                system_abstentions += 1

                if claim.label != "SUPPORTED":
                    correct_abstentions += 1

    annotation_complete = (
        annotated_claims == total_claims
    )

    return {
        "e2e_completion_rate": safe_divide(
            completed_cases,
            total_cases,
        ),
        "strict_supported_recall": safe_divide(
            supported_presented,
            supported_total,
        ),
        "observed_supported_recall": (
            safe_divide(
                supported_presented,
                observable_supported,
            )
        ),
        "unobservable_claim_rate": safe_divide(
            not_reached,
            total_claims,
        ),
        "safe_claim_coverage": safe_divide(
            supported_presented,
            total_claims,
        ),
        "abstention_precision": safe_divide(
            correct_abstentions,
            system_abstentions,
        ),
        "abstention_recall": safe_divide(
            correct_abstentions,
            required_abstentions,
        ),
        "unsafe_presented": (
            unsafe_presented
        ),
        "completed_cases": (
            completed_cases
        ),
        "total_cases": total_cases,
        "annotated_cases": len(
            annotations
        ),
        "annotated_claims": (
            annotated_claims
        ),
        "annotation_complete": (
            annotation_complete
        ),
        "supported_presented": (
            supported_presented
        ),
        "supported_total": (
            supported_total
        ),
        "observable_supported": (
            observable_supported
        ),
        "not_reached": not_reached,
        "total_claims": total_claims,
        "correct_abstentions": (
            correct_abstentions
        ),
        "system_abstentions": (
            system_abstentions
        ),
        "required_abstentions": (
            required_abstentions
        ),
    }


def format_rate(
    value: float | None,
) -> str:
    if value is None:
        return "N/A"

    return f"{value:.3f}"


def print_report(
    ground_truth: dict[str, int],
    exposure: dict[str, int],
    metrics: dict[
        str,
        float | int | bool | None,
    ],
) -> None:
    print("HOLDOUT V1 SCORING")

    print()
    print("Ground Truth")
    print("------------")
    print(
        f"Cases:                 "
        f"{ground_truth['cases']}"
    )
    print(
        f"Total claims:          "
        f"{ground_truth['total_claims']}"
    )
    print(
        f"SUPPORTED:             "
        f"{ground_truth['supported']}"
    )
    print(
        f"UNSUPPORTED:           "
        f"{ground_truth['unsupported']}"
    )
    print(
        f"AMBIGUOUS:             "
        f"{ground_truth['ambiguous']}"
    )
    print(
        f"CONFLICTING:           "
        f"{ground_truth['conflicting']}"
    )
    print(
        f"Required abstentions:  "
        f"{ground_truth['required_abstentions']}"
    )

    print()
    print("Exposure")
    print("--------")

    for status in (
        "PRESENTED",
        "ABSTAINED",
        "NOT_REACHED",
        "UNSAFE_PRESENTED",
        "NOT_APPLICABLE",
        "UNANNOTATED",
    ):
        print(
            f"{status + ':':22}"
            f"{exposure.get(status, 0)}"
        )

    print()
    print("Annotation")
    print("----------")
    print(
        f"Annotated cases:        "
        f"{metrics['annotated_cases']}/"
        f"{metrics['total_cases']}"
    )
    print(
        f"Annotated claims:       "
        f"{metrics['annotated_claims']}/"
        f"{metrics['total_claims']}"
    )
    print(
        f"Annotation complete:    "
        f"{metrics['annotation_complete']}"
    )

    print()
    print("Metrics")
    print("-------")
    print(
        "E2E completion:         "
        + format_rate(
            metrics[
                "e2e_completion_rate"
            ]
        )
    )
    print(
        "Strict supported recall: "
        + format_rate(
            metrics[
                "strict_supported_recall"
            ]
        )
    )
    print(
        "Observed supported recall: "
        + format_rate(
            metrics[
                "observed_supported_recall"
            ]
        )
    )
    print(
        "Unobservable claim rate: "
        + format_rate(
            metrics[
                "unobservable_claim_rate"
            ]
        )
    )
    print(
        "Safe claim coverage:     "
        + format_rate(
            metrics[
                "safe_claim_coverage"
            ]
        )
    )
    print(
        "Abstention precision:    "
        + format_rate(
            metrics[
                "abstention_precision"
            ]
        )
    )
    print(
        "Abstention recall:       "
        + format_rate(
            metrics[
                "abstention_recall"
            ]
        )
    )
    print(
        f"Unsafe presented:        "
        f"{metrics['unsafe_presented']}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate and aggregate "
            "Why-Blame Holdout v1 "
            "scoring annotations."
        )
    )

    parser.add_argument(
        "--holdout-dir",
        type=Path,
        default=(
            Path(__file__)
            .resolve()
            .parent
        ),
    )

    parser.add_argument(
        "--implementation-commit",
        default=(
            DEFAULT_IMPLEMENTATION_COMMIT
        ),
    )

    return parser


def main() -> None:
    args = build_parser().parse_args()

    holdout_dir = args.holdout_dir

    cases_dir = (
        holdout_dir / "cases"
    )

    results_dir = (
        holdout_dir / "results"
    )

    scoring_dir = (
        holdout_dir / "scoring"
    )

    cases = discover_cases(
        cases_dir
    )

    results = discover_results(
        results_dir
    )

    annotations = discover_annotations(
        scoring_dir
    )

    validate_benchmark(
        cases,
        results,
        annotations,
        args.implementation_commit,
    )

    ground_truth = (
        summarize_ground_truth(
            cases
        )
    )

    exposure = summarize_exposure(
        cases,
        annotations,
    )

    metrics = compute_metrics(
        cases,
        annotations,
    )

    print_report(
        ground_truth,
        exposure,
        metrics,
    )


if __name__ == "__main__":
    main()