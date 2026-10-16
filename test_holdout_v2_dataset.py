import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from benchmark.holdout_v2.dataset import (
    DatasetError,
    validate_dataset,
)


REPOSITORY_URL = "https://example.com/httpx.git"
REPOSITORY_COMMIT = "a" * 40


def make_candidate(
    candidate_id="httpx_001",
    case_file="cases/httpx_001.json",
    result_file="results/httpx_001.json",
    annotation_file="annotations/httpx_001.json",
):
    return SimpleNamespace(
        schema_version=2,
        candidate_id=candidate_id,
        repository=SimpleNamespace(
            url=REPOSITORY_URL,
            commit=REPOSITORY_COMMIT,
        ),
        artifacts=SimpleNamespace(
            case_file=case_file,
            result_file=result_file,
            annotation_file=annotation_file,
        ),
    )


def write_json(root, relative_path, data):
    path = Path(root) / relative_path

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            data,
            indent=2,
        ),
        encoding="utf-8",
    )

    return path


def write_case(root, case_id="httpx_001"):
    return write_json(
        root,
        "cases/httpx_001.json",
        {
            "schema_version": 2,
            "case_id": case_id,
            "repository": {
                "url": REPOSITORY_URL,
                "commit": REPOSITORY_COMMIT,
            },
            "frozen": True,
            "claims": {
                "claim_001": {
                    "type": "BEHAVIOR",
                    "label": "SUPPORTED",
                    "text": (
                        "The target performs the "
                        "observed behavior."
                    ),
                    "evidence": [
                        {
                            "channel": "DIFF",
                            "ref": (
                                "https://example.com/"
                                "commit/aaaaaaaa"
                            ),
                            "relation": "SUPPORTS",
                            "note": (
                                "The frozen diff directly "
                                "shows the behavior."
                            ),
                        },
                    ],
                    "rationale": (
                        "The frozen public diff directly "
                        "establishes the behavior."
                    ),
                },
            },
        },
    )


def write_annotation(root, case_id="httpx_001"):
    return write_json(
        root,
        "annotations/httpx_001.json",
        {
            "schema_version": 2,
            "case_id": case_id,
            "execution": {
                "completed": True,
                "failure_stage": "",
                "failure_type": "",
            },
            "confidence": {
                "level": "VERY_HIGH",
                "source": "final_output",
            },
            "claims": {
                "claim_001": {
                    "status": "PRESENTED",
                    "raw_evidence": "Observed output",
                },
            },
        },
    )


def write_result(root):
    return write_json(
        root,
        "results/httpx_001.json",
        {
            "schema_version": 2,
            "case_id": "httpx_001",
        },
    )


def write_result_directory(root):
    result_dir = (
        Path(root)
        / "results"
        / "httpx_001"
    )
    result_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    stdout_path = (
        result_dir / "stdout.txt"
    )
    stdout_path.write_text(
        "Observed output",
        encoding="utf-8",
    )

    write_json(
        root,
        "results/httpx_001/metadata.json",
        {
            "schema_version": 2,
            "case_id": "httpx_001",
        },
    )

    return stdout_path


class TestHoldoutV2Dataset(unittest.TestCase):

    def test_validates_complete_dataset(self):
        with tempfile.TemporaryDirectory() as temp:
            write_case(temp)
            write_result(temp)
            write_annotation(temp)

            dataset = validate_dataset(
                [make_candidate()],
                temp,
            )

            self.assertEqual(
                len(dataset.artifacts),
                1,
            )

            self.assertEqual(
                dataset.artifacts[0].case.case_id,
                "httpx_001",
            )

            self.assertIsNotNone(
                dataset.artifacts[0].annotation,
            )

    def test_accepts_metadata_for_registered_result_directory(
        self,
    ):
        with tempfile.TemporaryDirectory() as temp:
            write_case(temp)
            write_result_directory(temp)
            write_annotation(temp)

            dataset = validate_dataset(
                [
                    make_candidate(
                        result_file=(
                            "results/httpx_001/"
                            "stdout.txt"
                        ),
                    ),
                ],
                temp,
            )

            self.assertEqual(
                len(dataset.artifacts),
                1,
            )

    def test_rejects_missing_result_file(self):
        with tempfile.TemporaryDirectory() as temp:
            write_case(temp)
            write_annotation(temp)

            with self.assertRaisesRegex(
                DatasetError,
                "result_file does not exist",
            ):
                validate_dataset(
                    [make_candidate()],
                    temp,
                )

    def test_rejects_orphan_case_file(self):
        with tempfile.TemporaryDirectory() as temp:
            write_case(temp)
            write_result(temp)
            write_annotation(temp)

            write_json(
                temp,
                "cases/orphan_001.json",
                {},
            )

            with self.assertRaisesRegex(
                DatasetError,
                "orphan artifact",
            ):
                validate_dataset(
                    [make_candidate()],
                    temp,
                )

    def test_rejects_orphan_result_file(self):
        with tempfile.TemporaryDirectory() as temp:
            write_case(temp)
            write_result(temp)
            write_annotation(temp)

            write_json(
                temp,
                "results/orphan_001.json",
                {},
            )

            with self.assertRaisesRegex(
                DatasetError,
                "orphan artifact",
            ):
                validate_dataset(
                    [make_candidate()],
                    temp,
                )

    def test_rejects_orphan_annotation_file(self):
        with tempfile.TemporaryDirectory() as temp:
            write_case(temp)
            write_result(temp)
            write_annotation(temp)

            write_json(
                temp,
                "annotations/orphan_001.json",
                {},
            )

            with self.assertRaisesRegex(
                DatasetError,
                "orphan artifact",
            ):
                validate_dataset(
                    [make_candidate()],
                    temp,
                )

    def test_rejects_duplicate_candidate_id(self):
        with tempfile.TemporaryDirectory() as temp:
            write_case(temp)
            write_result(temp)
            write_annotation(temp)

            with self.assertRaisesRegex(
                DatasetError,
                "duplicate candidate_id",
            ):
                validate_dataset(
                    [
                        make_candidate(),
                        make_candidate(),
                    ],
                    temp,
                )


if __name__ == "__main__":
    unittest.main()
