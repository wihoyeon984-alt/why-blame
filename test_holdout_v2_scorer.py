import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCORER = Path(
    "benchmark/holdout_v2/"
    "score_holdout_v2.py"
)


def write_json(path, data):
    path.write_text(
        json.dumps(
            data,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )


def make_case():
    return {
        "schema_version": 2,
        "case_id": "example_001",
        "repository": {
            "url": (
                "https://github.com/"
                "example/project.git"
            ),
            "commit": "abc123",
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
                        "ref": "abc123",
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
            "claim_002": {
                "type": "CAUSE",
                "label": "UNSUPPORTED",
                "text": (
                    "The change was introduced primarily "
                    "for performance."
                ),
                "evidence": [],
                "rationale": (
                    "The frozen evidence does not establish "
                    "this motivation."
                ),
            },
        },
    }


def make_annotation():
    return {
        "schema_version": 2,
        "case_id": "example_001",
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
                "raw_evidence": "Exact output",
            },
            "claim_002": {
                "status": "WITHHELD",
                "raw_evidence": "",
            },
        },
    }


class TestHoldoutV2Scorer(unittest.TestCase):

    def run_scorer(
        self,
        cases,
        annotations,
    ):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases_dir = root / "cases"
            scoring_dir = root / "scoring"

            cases_dir.mkdir()
            scoring_dir.mkdir()

            for name, data in cases.items():
                write_json(
                    cases_dir / name,
                    data,
                )

            for name, data in annotations.items():
                write_json(
                    scoring_dir / name,
                    data,
                )

            return subprocess.run(
                [
                    sys.executable,
                    str(SCORER),
                    "--cases-dir",
                    str(cases_dir),
                    "--scoring-dir",
                    str(scoring_dir),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

    def test_scores_valid_case_and_annotation(self):
        result = self.run_scorer(
            {
                "example_001.json": make_case(),
            },
            {
                "example_001.json": (
                    make_annotation()
                ),
            },
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=result.stdout + result.stderr,
        )
        self.assertIn(
            "Confidence-stratified metrics",
            result.stdout,
        )
        self.assertIn(
            "VERY_HIGH",
            result.stdout,
        )
        self.assertIn(
            "Claim precision:           1.000",
            result.stdout,
        )
        self.assertIn(
            "Supported recall:          1.000",
            result.stdout,
        )
        self.assertIn(
            "WITHHELD reason coverage",
            result.stdout,
        )
        self.assertIn(
            "Total WITHHELD:        1",
            result.stdout,
        )
        self.assertIn(
            "Reason specified:      0",
            result.stdout,
        )
        self.assertIn(
            "Reason unspecified:    1",
            result.stdout,
        )

    def test_rejects_missing_annotation(self):
        result = self.run_scorer(
            {
                "example_001.json": make_case(),
            },
            {},
        )

        self.assertNotEqual(
            result.returncode,
            0,
        )
        self.assertIn(
            "missing annotations",
            result.stderr,
        )

    def test_rejects_unknown_annotation(self):
        annotation = make_annotation()
        annotation["case_id"] = "unknown_001"

        result = self.run_scorer(
            {
                "example_001.json": make_case(),
            },
            {
                "unknown_001.json": annotation,
            },
        )

        self.assertNotEqual(
            result.returncode,
            0,
        )
        self.assertIn(
            "unknown annotations",
            result.stderr,
        )


if __name__ == "__main__":
    unittest.main()
