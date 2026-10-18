import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from benchmark.holdout_v2.score_holdout_v2 import (
    ScoringError,
    run as run_holdout_v2,
)


EXPANSION_ROOT = Path(
    "benchmark/holdout_v2_expansion"
)

DEFAULT_CASES_DIR = EXPANSION_ROOT / "cases"
DEFAULT_ANNOTATIONS_DIR = (
    EXPANSION_ROOT / "annotations"
)


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Score the isolated Holdout v2 "
            "expansion cohort."
        )
    )

    parser.add_argument(
        "--cases-dir",
        type=Path,
        default=DEFAULT_CASES_DIR,
    )

    parser.add_argument(
        "--annotations-dir",
        type=Path,
        default=DEFAULT_ANNOTATIONS_DIR,
    )

    return parser


def run(cases_dir, annotations_dir):
    frozen_root = Path(
        "benchmark/holdout_v2"
    ).resolve()

    resolved_cases = cases_dir.resolve()
    resolved_annotations = (
        annotations_dir.resolve()
    )

    if (
        resolved_cases == frozen_root
        or frozen_root in resolved_cases.parents
        or resolved_annotations == frozen_root
        or frozen_root
        in resolved_annotations.parents
    ):
        raise ScoringError(
            "the expansion scorer cannot read "
            "the frozen Holdout v2 directories"
        )

    run_holdout_v2(
        cases_dir=cases_dir,
        scoring_dir=annotations_dir,
    )


def main(argv=None):
    args = build_parser().parse_args(argv)

    try:
        run(
            cases_dir=args.cases_dir,
            annotations_dir=(
                args.annotations_dir
            ),
        )
    except (ValueError, OSError) as exc:
        print(
            "Holdout v2 expansion scoring "
            f"failed: {exc}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
