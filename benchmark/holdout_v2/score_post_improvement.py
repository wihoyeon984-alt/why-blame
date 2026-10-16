import argparse
import hashlib
import json
import math
import sys
from pathlib import Path


class PostImprovementError(Exception):
    pass


def _load_json(
    path,
    *,
    allow_bom=False,
):
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise PostImprovementError(
            f"Failed to read {path}: {exc}"
        ) from exc

    has_bom = raw.startswith(
        bytes([239, 187, 191])
    )

    if has_bom and not allow_bom:
        raise PostImprovementError(
            f"Unexpected UTF-8 BOM: {path}"
        )

    encoding = (
        "utf-8-sig"
        if allow_bom
        else "utf-8"
    )

    try:
        return json.loads(
            raw.decode(encoding)
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PostImprovementError(
            f"Invalid UTF-8 JSON: {path}: {exc}"
        ) from exc


def _safe_divide(numerator, denominator, default):
    if denominator == 0:
        return default

    return numerator / denominator


def _score_annotations(
    *,
    cases,
    annotations,
):
    metrics = {
        "case_count": 0,
        "supported_total": 0,
        "supported_presented": 0,
        "total_presentations": 0,
        "unsafe_presented": 0,
    }

    for case_id in sorted(cases):
        case = cases[case_id]
        annotation = annotations.get(case_id)

        if annotation is None:
            raise PostImprovementError(
                f"Missing annotation for {case_id}"
            )

        if annotation.get("case_id") != case_id:
            raise PostImprovementError(
                f"Annotation case ID mismatch: {case_id}"
            )

        case_claims = case.get("claims", {})
        annotation_claims = annotation.get(
            "claims",
            {},
        )

        if set(case_claims) != set(annotation_claims):
            raise PostImprovementError(
                f"Claim ID mismatch: {case_id}"
            )

        metrics["case_count"] += 1

        for claim_id, claim in case_claims.items():
            label = claim.get("label")
            status = annotation_claims[
                claim_id
            ].get("status")

            if label not in {
                "SUPPORTED",
                "UNSUPPORTED",
            }:
                raise PostImprovementError(
                    f"Invalid claim label: "
                    f"{case_id}/{claim_id}"
                )

            if status not in {
                "PRESENTED",
                "WITHHELD",
            }:
                raise PostImprovementError(
                    f"Invalid annotation status: "
                    f"{case_id}/{claim_id}"
                )

            if label == "SUPPORTED":
                metrics["supported_total"] += 1

                if status == "PRESENTED":
                    metrics[
                        "supported_presented"
                    ] += 1

            if status == "PRESENTED":
                metrics["total_presentations"] += 1

                if label == "UNSUPPORTED":
                    metrics["unsafe_presented"] += 1

    metrics["claim_precision"] = _safe_divide(
        (
            metrics["total_presentations"]
            - metrics["unsafe_presented"]
        ),
        metrics["total_presentations"],
        1.0,
    )

    metrics["supported_recall"] = _safe_divide(
        metrics["supported_presented"],
        metrics["supported_total"],
        1.0,
    )

    metrics[
        "unsafe_presentation_rate"
    ] = _safe_divide(
        metrics["unsafe_presented"],
        metrics["total_presentations"],
        0.0,
    )

    return metrics


def _compare_number(
    *,
    observed,
    expected,
    label,
):
    if isinstance(expected, float):
        if not math.isclose(
            observed,
            expected,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise PostImprovementError(
                f"{label} mismatch: "
                f"{observed!r} != {expected!r}"
            )

        return

    if observed != expected:
        raise PostImprovementError(
            f"{label} mismatch: "
            f"{observed!r} != {expected!r}"
        )


def _validate_metadata(
    *,
    case_id,
    post_dir,
    post_annotation,
):
    case_dir = post_dir / case_id
    metadata_path = case_dir / "metadata.json"
    stdout_path = case_dir / "stdout.txt"
    stderr_path = case_dir / "stderr.txt"

    for path in (
        metadata_path,
        stdout_path,
        stderr_path,
    ):
        if not path.exists():
            raise PostImprovementError(
                f"Missing artifact: {path}"
            )

    metadata = _load_json(metadata_path)
    stdout_bytes = stdout_path.read_bytes()

    try:
        stdout = stdout_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PostImprovementError(
            f"Invalid UTF-8 stdout: {stdout_path}"
        ) from exc

    if stderr_path.stat().st_size != 0:
        raise PostImprovementError(
            f"Non-empty stderr: {case_id}"
        )

    if metadata.get("case_id") != case_id:
        raise PostImprovementError(
            f"Metadata case ID mismatch: {case_id}"
        )

    if metadata.get("evaluation_type") != (
        "post_improvement_rerun"
    ):
        raise PostImprovementError(
            f"Invalid evaluation type: {case_id}"
        )

    if metadata.get("baseline_preserved") is not True:
        raise PostImprovementError(
            f"Baseline is not marked preserved: {case_id}"
        )

    execution = metadata.get("execution", {})

    if execution.get("exit_code") != 0:
        raise PostImprovementError(
            f"Nonzero exit code: {case_id}"
        )

    scoring_tier = execution.get("scoring_tier")
    annotation_level = post_annotation.get(
        "confidence",
        {},
    ).get("level")

    if scoring_tier != annotation_level:
        raise PostImprovementError(
            f"Confidence tier mismatch: {case_id}"
        )

    expected_hash = metadata.get(
        "artifacts",
        {},
    ).get("stdout_sha256")

    actual_hash = hashlib.sha256(
        stdout_bytes
    ).hexdigest()

    if actual_hash != expected_hash:
        raise PostImprovementError(
            f"stdout SHA-256 mismatch: {case_id}"
        )

    runtime_confidence = execution.get(
        "runtime_confidence"
    )

    if (
        not runtime_confidence
        or (
            "CONFIDENCE:  "
            + runtime_confidence
        )
        not in stdout
    ):
        raise PostImprovementError(
            f"Runtime confidence missing: {case_id}"
        )

    return metadata


def evaluate_post_improvement(
    *,
    holdout_dir,
    post_dir,
):
    holdout_dir = Path(holdout_dir)
    post_dir = Path(post_dir)

    if not holdout_dir.is_dir():
        raise PostImprovementError(
            f"Holdout directory does not exist: "
            f"{holdout_dir}"
        )

    if not post_dir.is_dir():
        raise PostImprovementError(
            f"Post-improvement directory does not exist: "
            f"{post_dir}"
        )

    cases_dir = holdout_dir / "cases"
    baseline_dir = holdout_dir / "annotations"
    post_annotation_dir = (
        post_dir / "annotations"
    )
    summary_path = post_dir / "summary.json"

    if not post_annotation_dir.is_dir():
        raise PostImprovementError(
            "Post-improvement annotations are missing"
        )

    if not summary_path.exists():
        raise PostImprovementError(
            "Post-improvement summary is missing"
        )

    cases = {}
    baseline_annotations = {}

    for case_path in sorted(cases_dir.glob("*.json")):
        case = _load_json(
            case_path,
            allow_bom=True,
        )
        case_id = case.get("case_id")

        if not case_id:
            raise PostImprovementError(
                f"Missing case_id: {case_path}"
            )

        cases[case_id] = case

        baseline_path = (
            baseline_dir / f"{case_id}.json"
        )

        if not baseline_path.exists():
            raise PostImprovementError(
                f"Missing baseline annotation: "
                f"{case_id}"
            )

        baseline_annotations[case_id] = (
            _load_json(
                baseline_path,
                allow_bom=True,
            )
        )

    post_files = sorted(
        post_annotation_dir.glob("*.json")
    )

    if not post_files:
        raise PostImprovementError(
            "No post-improvement annotations found"
        )

    post_annotations = dict(
        baseline_annotations
    )

    post_overrides = {}

    for annotation_path in post_files:
        annotation = _load_json(annotation_path)
        case_id = annotation.get("case_id")

        if case_id not in cases:
            raise PostImprovementError(
                f"Unknown post-improvement case: "
                f"{case_id}"
            )

        post_overrides[case_id] = annotation
        post_annotations[case_id] = annotation

        _validate_metadata(
            case_id=case_id,
            post_dir=post_dir,
            post_annotation=annotation,
        )

    baseline_metrics = _score_annotations(
        cases=cases,
        annotations=baseline_annotations,
    )

    post_metrics = _score_annotations(
        cases=cases,
        annotations=post_annotations,
    )

    improvements = []

    for case_id in sorted(post_overrides):
        case_claims = cases[case_id]["claims"]
        baseline_claims = baseline_annotations[
            case_id
        ]["claims"]
        post_claims = post_overrides[
            case_id
        ]["claims"]

        if set(case_claims) != set(post_claims):
            raise PostImprovementError(
                f"Post claim ID mismatch: {case_id}"
            )

        changed = []

        for claim_id, claim in case_claims.items():
            baseline_status = baseline_claims[
                claim_id
            ]["status"]
            post_status = post_claims[
                claim_id
            ]["status"]

            if baseline_status == post_status:
                continue

            changed.append(
                {
                    "case_id": case_id,
                    "claim_id": claim_id,
                    "label": claim["label"],
                    "baseline_status": (
                        baseline_status
                    ),
                    "post_improvement_status": (
                        post_status
                    ),
                }
            )

        if len(changed) != 1:
            raise PostImprovementError(
                f"Expected exactly one changed claim "
                f"for {case_id}, got {changed}"
            )

        item = changed[0]

        if (
            item["label"] != "SUPPORTED"
            or item["baseline_status"]
            != "WITHHELD"
            or item["post_improvement_status"]
            != "PRESENTED"
        ):
            raise PostImprovementError(
                f"Unsafe improvement: {item}"
            )

        improvements.append(item)

    delta = {
        "supported_presented": (
            post_metrics["supported_presented"]
            - baseline_metrics[
                "supported_presented"
            ]
        ),
        "total_presentations": (
            post_metrics["total_presentations"]
            - baseline_metrics[
                "total_presentations"
            ]
        ),
        "unsafe_presented": (
            post_metrics["unsafe_presented"]
            - baseline_metrics["unsafe_presented"]
        ),
        "claim_precision": (
            post_metrics["claim_precision"]
            - baseline_metrics["claim_precision"]
        ),
        "supported_recall": (
            post_metrics["supported_recall"]
            - baseline_metrics["supported_recall"]
        ),
        "unsafe_presentation_rate": (
            post_metrics[
                "unsafe_presentation_rate"
            ]
            - baseline_metrics[
                "unsafe_presentation_rate"
            ]
        ),
    }

    result = {
        "baseline": baseline_metrics,
        "post_improvement": post_metrics,
        "delta": delta,
        "improvements": improvements,
    }

    preserved_summary = _load_json(
        summary_path
    )

    for section in (
        "baseline",
        "post_improvement",
        "delta",
    ):
        expected = preserved_summary.get(
            section,
            {}
        )
        observed = result[section]

        for key, expected_value in expected.items():
            if key not in observed:
                raise PostImprovementError(
                    f"Missing calculated field: "
                    f"{section}.{key}"
                )

            _compare_number(
                observed=observed[key],
                expected=expected_value,
                label=f"{section}.{key}",
            )

    preserved_improvements = [
        (
            item.get("case_id"),
            item.get("claim_id"),
            item.get("label"),
            item.get("baseline_status"),
            item.get(
                "post_improvement_status"
            ),
        )
        for item in preserved_summary.get(
            "improvements",
            [],
        )
    ]

    calculated_improvements = [
        (
            item["case_id"],
            item["claim_id"],
            item["label"],
            item["baseline_status"],
            item[
                "post_improvement_status"
            ],
        )
        for item in improvements
    ]

    if (
        preserved_improvements
        != calculated_improvements
    ):
        raise PostImprovementError(
            "Preserved improvement list does not "
            "match calculated improvements"
        )

    if post_metrics["unsafe_presented"] != 0:
        raise PostImprovementError(
            "Post-improvement evaluation contains "
            "unsafe presentations"
        )

    return result


def render_comparison(result):
    baseline = result["baseline"]
    post = result["post_improvement"]
    delta = result["delta"]

    return "\n".join(
        [
            "Holdout v2 post-improvement comparison",
            "---------------------------------------",
            "",
            "Baseline",
            (
                "  Supported presented:       "
                f"{baseline['supported_presented']} / "
                f"{baseline['supported_total']}"
            ),
            (
                "  Claim precision:           "
                f"{baseline['claim_precision']:.3f}"
            ),
            (
                "  Supported recall:          "
                f"{baseline['supported_recall']:.3f}"
            ),
            (
                "  Unsafe presentation rate:  "
                f"{baseline['unsafe_presentation_rate']:.3f}"
            ),
            "",
            "Post-improvement",
            (
                "  Supported presented:       "
                f"{post['supported_presented']} / "
                f"{post['supported_total']}"
            ),
            (
                "  Claim precision:           "
                f"{post['claim_precision']:.3f}"
            ),
            (
                "  Supported recall:          "
                f"{post['supported_recall']:.3f}"
            ),
            (
                "  Unsafe presentation rate:  "
                f"{post['unsafe_presentation_rate']:.3f}"
            ),
            "",
            "Delta",
            (
                "  Supported presented:       "
                f"{delta['supported_presented']:+d}"
            ),
            (
                "  Supported recall:          "
                f"{delta['supported_recall']:+.3f}"
            ),
            (
                "  Unsafe presented:          "
                f"{delta['unsafe_presented']:+d}"
            ),
        ]
    )


def build_parser():
    default_holdout = Path(__file__).parent
    default_post = (
        default_holdout
        / "post_improvement"
    )

    parser = argparse.ArgumentParser(
        description=(
            "Validate and report Holdout v2 "
            "post-improvement evaluation."
        )
    )

    parser.add_argument(
        "--holdout-dir",
        type=Path,
        default=default_holdout,
    )
    parser.add_argument(
        "--post-dir",
        type=Path,
        default=default_post,
    )

    return parser


def run(argv=None):
    args = build_parser().parse_args(argv)

    result = evaluate_post_improvement(
        holdout_dir=args.holdout_dir,
        post_dir=args.post_dir,
    )

    return render_comparison(result)


def main(argv=None):
    try:
        rendered = run(argv)
    except PostImprovementError as exc:
        print(
            "Holdout v2 post-improvement scoring "
            f"failed: {exc}",
            file=sys.stderr,
        )
        return 1

    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
