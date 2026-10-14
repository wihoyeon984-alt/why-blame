import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from benchmark.holdout_v2.annotation import (
    load_annotation,
)
from benchmark.holdout_v2.case import (
    load_case,
)
from benchmark.holdout_v2.metrics import (
    compute_confidence_metrics,
)
from benchmark.holdout_v2.report import (
    print_confidence_metrics,
)


class ScoringError(ValueError):
    pass


def discover_files(directory):
    return sorted(
        path
        for path in directory.glob("*.json")
        if path.name != "SCORING_TEMPLATE.json"
    )


def load_cases(directory):
    cases = {}

    for path in discover_files(directory):
        case = load_case(path)

        if case.case_id in cases:
            raise ScoringError(
                "duplicate case_id: "
                f"{case.case_id}"
            )

        cases[case.case_id] = case

    return cases


def load_annotations(directory):
    annotations = {}

    for path in discover_files(directory):
        annotation = load_annotation(path)

        if annotation.case_id in annotations:
            raise ScoringError(
                "duplicate annotation case_id: "
                f"{annotation.case_id}"
            )

        annotations[
            annotation.case_id
        ] = annotation

    return annotations


def validate_case_sets(
    cases,
    annotations,
):
    case_ids = set(cases)
    annotation_ids = set(annotations)

    missing = sorted(
        case_ids - annotation_ids
    )

    unknown = sorted(
        annotation_ids - case_ids
    )

    errors = []

    if missing:
        errors.append(
            "missing annotations: "
            + ", ".join(missing)
        )

    if unknown:
        errors.append(
            "unknown annotations: "
            + ", ".join(unknown)
        )

    if errors:
        raise ScoringError(
            "; ".join(errors)
        )


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Score Holdout v2 annotations "
            "by confidence level."
        )
    )

    parser.add_argument(
        "--cases-dir",
        type=Path,
        default=Path(
            "benchmark/holdout_v2/cases"
        ),
    )

    parser.add_argument(
        "--scoring-dir",
        type=Path,
        default=Path(
            "benchmark/holdout_v2/annotations"
        ),
    )

    return parser


def run(cases_dir, scoring_dir):
    cases = load_cases(cases_dir)
    annotations = load_annotations(
        scoring_dir
    )

    if not cases:
        raise ScoringError(
            "no Holdout v2 cases found"
        )

    validate_case_sets(
        cases,
        annotations,
    )

    metrics = compute_confidence_metrics(
        list(cases.values()),
        annotations,
    )

    print_confidence_metrics(metrics)


def main():
    args = build_parser().parse_args()

    try:
        run(
            args.cases_dir,
            args.scoring_dir,
        )
    except (ValueError, OSError) as exc:
        print(
            f"Holdout v2 scoring failed: {exc}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
