import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXPANSION_ROOT = Path(
    "benchmark/holdout_v2_expansion"
)
FROZEN_HOLDOUT_ROOT = Path(
    "benchmark/holdout_v2"
)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from benchmark.holdout_v2.annotation import (
    load_annotation,
)
from benchmark.holdout_v2.case import load_case
from benchmark.holdout_v2.validation import (
    validate_annotation_against_case,
)


class ExpansionValidationError(ValueError):
    pass


TEMPLATE_MARKERS = (
    "example_001",
    "example/project.git",
    "abc123",
    "project_001",
    "Exact supporting output",
)


def _load_json(path):
    try:
        return json.loads(
            path.read_text(encoding="utf-8-sig")
        )
    except json.JSONDecodeError as exc:
        raise ExpansionValidationError(
            f"{path}: invalid JSON"
        ) from exc


def _discover_json_ids(directory):
    result = {}

    if not directory.is_dir():
        raise ExpansionValidationError(
            f"missing directory: {directory}"
        )

    for path in sorted(directory.glob("*.json")):
        item_id = path.stem

        if item_id in result:
            raise ExpansionValidationError(
                f"duplicate artifact ID: {item_id}"
            )

        result[item_id] = path

    return result


def _require_matching_ids(cases, annotations):
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
        raise ExpansionValidationError(
            "; ".join(errors)
        )


def _reject_template_markers(path):
    text = path.read_text(encoding="utf-8-sig")

    for marker in TEMPLATE_MARKERS:
        if marker in text:
            raise ExpansionValidationError(
                f"{path}: template marker remains: "
                f"{marker}"
            )


def _require_string(document, key, label):
    value = document.get(key)

    if not isinstance(value, str) or not value:
        raise ExpansionValidationError(
            f"{label} must be a non-empty string"
        )

    return value


def _sha256(path):
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def _git_output(arguments, repository_root):
    result = subprocess.run(
        ["git", *arguments],
        cwd=repository_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    if result.returncode != 0:
        message = result.stderr.strip()

        raise ExpansionValidationError(
            "Git command failed: "
            + (" ".join(arguments))
            + (
                f": {message}"
                if message
                else ""
            )
        )

    return result.stdout.strip()


def _commit_for_path(
    repository_root,
    relative_path,
):
    commit = _git_output(
        [
            "log",
            "-1",
            "--format=%H",
            "--",
            relative_path.as_posix(),
        ],
        repository_root,
    )

    if not commit:
        raise ExpansionValidationError(
            f"no Git commit found for {relative_path}"
        )

    return commit


def _require_ancestor(
    repository_root,
    ancestor,
    descendant,
    label,
):
    result = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            ancestor,
            descendant,
        ],
        cwd=repository_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    if result.returncode == 0:
        return

    if result.returncode == 1:
        raise ExpansionValidationError(
            f"invalid commit order: {label}"
        )

    raise ExpansionValidationError(
        "Git ancestry check failed: "
        + result.stderr.strip()
    )


def validate_run_artifacts(
    expansion_root,
    case_id,
    case,
):
    run_dir = expansion_root / "runs" / case_id

    required_paths = {
        "metadata": run_dir / "metadata.json",
        "stdout_bin": run_dir / "stdout.bin",
        "stderr_bin": run_dir / "stderr.bin",
        "stdout_text": run_dir / "stdout.txt",
        "stderr_text": run_dir / "stderr.txt",
    }

    for label, path in required_paths.items():
        if not path.is_file():
            raise ExpansionValidationError(
                f"{case_id}: missing {label}: {path}"
            )

    metadata = _load_json(
        required_paths["metadata"]
    )

    if metadata.get("schema_version") != 1:
        raise ExpansionValidationError(
            f"{case_id}: run metadata "
            "schema_version must be 1"
        )

    if metadata.get("case_id") != case_id:
        raise ExpansionValidationError(
            f"{case_id}: metadata case_id mismatch"
        )

    source_repository = _require_string(
        metadata,
        "source_repository",
        f"{case_id}.source_repository",
    )
    source_commit = _require_string(
        metadata,
        "source_commit",
        f"{case_id}.source_commit",
    )
    target = _require_string(
        metadata,
        "target",
        f"{case_id}.target",
    )
    ground_truth_commit = _require_string(
        metadata,
        "ground_truth_commit",
        f"{case_id}.ground_truth_commit",
    )

    if source_repository != case.repository_url:
        raise ExpansionValidationError(
            f"{case_id}: source repository mismatch"
        )

    if source_commit != case.repository_commit:
        raise ExpansionValidationError(
            f"{case_id}: source commit mismatch"
        )

    if ":" not in target:
        raise ExpansionValidationError(
            f"{case_id}: invalid target"
        )

    for stream in ("stdout", "stderr"):
        binary_path = required_paths[
            f"{stream}_bin"
        ]
        expected_hash = _require_string(
            metadata,
            f"{stream}_sha256",
            f"{case_id}.{stream}_sha256",
        )
        actual_hash = _sha256(binary_path)

        if actual_hash != expected_hash:
            raise ExpansionValidationError(
                f"{case_id}: {stream} SHA-256 mismatch"
            )

        expected_size = metadata.get(
            f"{stream}_bytes"
        )

        if expected_size != len(
            binary_path.read_bytes()
        ):
            raise ExpansionValidationError(
                f"{case_id}: {stream} byte count mismatch"
            )

    exit_code = metadata.get("exit_code")

    if not isinstance(exit_code, int):
        raise ExpansionValidationError(
            f"{case_id}: exit_code must be an integer"
        )

    if exit_code == 0:
        output = _load_json(
            required_paths["stdout_text"]
        )

        if not isinstance(output, dict):
            raise ExpansionValidationError(
                f"{case_id}: stdout JSON "
                "must be an object"
            )

        if output.get("schema_version") != "1":
            raise ExpansionValidationError(
                f"{case_id}: unexpected output "
                "schema_version"
            )

    return {
        "metadata": metadata,
        "ground_truth_commit": (
            ground_truth_commit
        ),
        "stdout_sha256": metadata[
            "stdout_sha256"
        ],
        "stderr_sha256": metadata[
            "stderr_sha256"
        ],
    }


def validate_git_order(
    repository_root,
    expansion_root,
    case_id,
    ground_truth_commit,
):
    relative_root = expansion_root.relative_to(
        repository_root
    )

    case_path = (
        relative_root
        / "cases"
        / f"{case_id}.json"
    )
    run_path = (
        relative_root
        / "runs"
        / case_id
    )
    annotation_path = (
        relative_root
        / "annotations"
        / f"{case_id}.json"
    )

    case_commit = _commit_for_path(
        repository_root,
        case_path,
    )
    run_commit = _commit_for_path(
        repository_root,
        run_path,
    )
    annotation_commit = _commit_for_path(
        repository_root,
        annotation_path,
    )

    if case_commit != ground_truth_commit:
        raise ExpansionValidationError(
            f"{case_id}: metadata Ground Truth "
            "commit does not match case commit"
        )

    if len(
        {
            case_commit,
            run_commit,
            annotation_commit,
        }
    ) != 3:
        raise ExpansionValidationError(
            f"{case_id}: Ground Truth, first run, "
            "and annotation must use separate commits"
        )

    _require_ancestor(
        repository_root,
        case_commit,
        run_commit,
        f"{case_id} Ground Truth -> first run",
    )
    _require_ancestor(
        repository_root,
        run_commit,
        annotation_commit,
        f"{case_id} first run -> annotation",
    )

    return {
        "ground_truth_commit": case_commit,
        "first_run_commit": run_commit,
        "annotation_commit": annotation_commit,
    }


def validate_case(
    repository_root,
    expansion_root,
    case_id,
    case_path,
    annotation_path,
):
    _reject_template_markers(case_path)
    _reject_template_markers(annotation_path)

    case = load_case(case_path)
    annotation = load_annotation(
        annotation_path
    )

    if case.case_id != case_id:
        raise ExpansionValidationError(
            f"{case_id}: case_id mismatch"
        )

    if annotation.case_id != case_id:
        raise ExpansionValidationError(
            f"{case_id}: annotation case_id mismatch"
        )

    validate_annotation_against_case(
        case,
        annotation,
    )

    run_result = validate_run_artifacts(
        expansion_root,
        case_id,
        case,
    )

    git_result = validate_git_order(
        repository_root,
        expansion_root,
        case_id,
        run_result["ground_truth_commit"],
    )

    statuses = Counter(
        claim.status
        for claim in annotation.claims.values()
    )
    specified_reasons = sum(
        1
        for claim in annotation.claims.values()
        if claim.withheld_reason
    )

    return {
        "case_id": case_id,
        "claim_count": len(case.claims),
        "confidence": annotation.confidence_level,
        "statuses": statuses,
        "specified_reasons": specified_reasons,
        **run_result,
        **git_result,
    }


def validate_expansion(
    expansion_root=DEFAULT_EXPANSION_ROOT,
    repository_root=ROOT,
):
    repository_root = repository_root.resolve()
    expansion_root = expansion_root.resolve()
    frozen_root = (
        repository_root / FROZEN_HOLDOUT_ROOT
    ).resolve()

    if (
        expansion_root == frozen_root
        or frozen_root in expansion_root.parents
    ):
        raise ExpansionValidationError(
            "the expansion validator cannot read "
            "the frozen Holdout v2 directory"
        )

    cases = _discover_json_ids(
        expansion_root / "cases"
    )
    annotations = _discover_json_ids(
        expansion_root / "annotations"
    )

    if not cases:
        raise ExpansionValidationError(
            "no expansion cases found"
        )

    _require_matching_ids(
        cases,
        annotations,
    )

    results = []

    for case_id in sorted(cases):
        results.append(
            validate_case(
                repository_root=repository_root,
                expansion_root=expansion_root,
                case_id=case_id,
                case_path=cases[case_id],
                annotation_path=annotations[
                    case_id
                ],
            )
        )

    return results


def render_results(results):
    lines = []

    for index, result in enumerate(results):
        if index:
            lines.append("")

        lines.append(result["case_id"])
        lines.append(
            "  Ground Truth: "
            + result["ground_truth_commit"][:7]
        )
        lines.append(
            "  First run:    "
            + result["first_run_commit"][:7]
        )
        lines.append(
            "  Annotation:   "
            + result["annotation_commit"][:7]
        )
        lines.append(
            "  stdout SHA-256: OK"
        )
        lines.append(
            "  stderr SHA-256: OK"
        )
        lines.append(
            f"  claims: {result['claim_count']}"
        )
        lines.append(
            f"  confidence: {result['confidence']}"
        )

        for status, count in sorted(
            result["statuses"].items()
        ):
            lines.append(
                f"  {status}: {count}"
            )

        lines.append(
            "  withheld reasons specified: "
            f"{result['specified_reasons']}"
        )

    lines.append("")
    lines.append(
        f"EXPANSION_CASES_VALID={len(results)}"
    )
    lines.append("EXPANSION_VALIDATION_OK")

    return "\n".join(lines)


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Validate the isolated Holdout v2 "
            "expansion cohort."
        )
    )

    parser.add_argument(
        "--expansion-root",
        type=Path,
        default=DEFAULT_EXPANSION_ROOT,
    )

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    try:
        results = validate_expansion(
            expansion_root=args.expansion_root,
            repository_root=ROOT,
        )
    except (
        ExpansionValidationError,
        ValueError,
        OSError,
    ) as exc:
        print(
            "Holdout v2 expansion validation "
            f"failed: {exc}",
            file=sys.stderr,
        )
        return 1

    print(render_results(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
