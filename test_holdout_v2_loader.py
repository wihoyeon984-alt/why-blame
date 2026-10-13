import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from benchmark.holdout_v2.loader import (
    LoaderError,
    load_candidate_artifacts,
)


REPOSITORY_URL = (
    "https://example.com/urllib3.git"
)
REPOSITORY_COMMIT = "a" * 40


def make_candidate(
    case_file="cases/urllib3_001.json",
    annotation_file="",
    candidate_id="urllib3_001",
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
            result_file="",
            annotation_file=annotation_file,
        ),
    )


def write_case(
    holdout_dir,
    case_id="urllib3_001",
):
    case_path = (
        Path(holdout_dir)
        / "cases"
        / "urllib3_001.json"
    )

    case_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    case_data = {
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
                    "The pinned fixture directly "
                    "establishes the behavior."
                ),
                "evidence": [
                    {
                        "channel": "DIFF",
                        "ref": REPOSITORY_COMMIT,
                        "relation": "SUPPORTS",
                        "note": (
                            "The frozen fixture diff "
                            "directly shows the behavior."
                        ),
                    },
                ],
                "rationale": (
                    "The behavior is directly observable "
                    "in the frozen evidence."
                ),
            },
        },
    }

    case_path.write_text(
        json.dumps(
            case_data,
            indent=2,
        ),
        encoding="utf-8",
    )

    return case_path


def write_annotation(
    holdout_dir,
    case_id="urllib3_001",
    claim_id="claim_001",
):
    annotation_path = (
        Path(holdout_dir)
        / "annotations"
        / "urllib3_001.json"
    )

    annotation_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    annotation_data = {
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
            claim_id: {
                "status": "PRESENTED",
                "raw_evidence": (
                    "Exact supporting output"
                ),
            },
        },
    }

    annotation_path.write_text(
        json.dumps(
            annotation_data,
            indent=2,
        ),
        encoding="utf-8",
    )

    return annotation_path


class TestHoldoutV2Loader(unittest.TestCase):

    def test_loads_valid_case_artifact(self):
        with tempfile.TemporaryDirectory() as temp:
            write_case(temp)

            loaded = load_candidate_artifacts(
                make_candidate(),
                temp,
            )

            self.assertEqual(
                loaded.case.case_id,
                "urllib3_001",
            )

            self.assertIsNone(
                loaded.annotation
            )

    def test_rejects_missing_case_file(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(
                LoaderError
            ):
                load_candidate_artifacts(
                    make_candidate(),
                    temp,
                )

    def test_rejects_parent_path(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(
                LoaderError
            ):
                load_candidate_artifacts(
                    make_candidate(
                        case_file=(
                            "../outside.json"
                        ),
                    ),
                    temp,
                )

    def test_rejects_absolute_path(self):
        with tempfile.TemporaryDirectory() as temp:
            absolute_path = (
                Path(temp)
                / "outside.json"
            ).resolve()

            with self.assertRaises(
                LoaderError
            ):
                load_candidate_artifacts(
                    make_candidate(
                        case_file=str(
                            absolute_path
                        ),
                    ),
                    temp,
                )

    def test_rejects_case_id_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            write_case(
                temp,
                case_id="urllib3_999",
            )

            with self.assertRaises(
                ValueError
            ):
                load_candidate_artifacts(
                    make_candidate(),
                    temp,
                )

    def test_loads_valid_annotation_artifact(self):
        with tempfile.TemporaryDirectory() as temp:
            write_case(temp)
            write_annotation(temp)

            loaded = load_candidate_artifacts(
                make_candidate(
                    annotation_file=(
                        "annotations/"
                        "urllib3_001.json"
                    ),
                ),
                temp,
            )

            self.assertIsNotNone(
                loaded.annotation
            )

            self.assertEqual(
                loaded.annotation.case_id,
                "urllib3_001",
            )

    def test_rejects_missing_annotation_file(self):
        with tempfile.TemporaryDirectory() as temp:
            write_case(temp)

            with self.assertRaises(
                LoaderError
            ):
                load_candidate_artifacts(
                    make_candidate(
                        annotation_file=(
                            "annotations/"
                            "missing.json"
                        ),
                    ),
                    temp,
                )

    def test_rejects_annotation_claim_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            write_case(temp)

            write_annotation(
                temp,
                claim_id="claim_999",
            )

            with self.assertRaises(
                ValueError
            ):
                load_candidate_artifacts(
                    make_candidate(
                        annotation_file=(
                            "annotations/"
                            "urllib3_001.json"
                        ),
                    ),
                    temp,
                )


if __name__ == "__main__":
    unittest.main()
