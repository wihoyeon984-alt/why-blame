import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from benchmark.holdout_v2.score_holdout_v2 import (
    ScoringError,
)
from benchmark.holdout_v2_expansion.score_expansion import (
    DEFAULT_ANNOTATIONS_DIR,
    DEFAULT_CASES_DIR,
    build_parser,
    run,
)


SCORER = Path(
    "benchmark/holdout_v2_expansion/"
    "score_expansion.py"
)


def write_json(path, document):
    path.write_text(
        json.dumps(
            document,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def make_case():
    return {
        "schema_version": 2,
        "case_id": "expansion_001",
        "repository": {
            "url": (
                "https://github.com/"
                "example/project.git"
            ),
            "commit": "a" * 40,
        },
        "frozen": True,
        "claims": {
            "claim_001": {
                "type": "BEHAVIOR",
                "label": "SUPPORTED",
                "text": (
                    "The preserved code performs "
                    "the observed behavior."
                ),
                "evidence": [
                    {
                        "channel": "DIFF",
                        "ref": "a" * 40,
                        "relation": "SUPPORTS",
                        "note": (
                            "The fixture directly "
                            "shows the behavior."
                        ),
                    },
                ],
                "rationale": (
                    "The behavior is directly "
                    "observable."
                ),
            },
            "claim_002": {
                "type": "CAUSE",
                "label": "UNSUPPORTED",
                "text": (
                    "The change was introduced "
                    "for performance."
                ),
                "evidence": [],
                "rationale": (
                    "The preserved evidence does "
                    "not establish this motive."
                ),
            },
        },
    }


def make_annotation():
    return {
        "schema_version": 2,
        "case_id": "expansion_001",
        "execution": {
            "completed": True,
            "failure_stage": "",
            "failure_type": "",
        },
        "confidence": {
            "level": "HIGH",
            "source": "final_output",
        },
        "claims": {
            "claim_001": {
                "status": "PRESENTED",
                "raw_evidence": (
                    "Exact supporting output"
                ),
            },
            "claim_002": {
                "status": "WITHHELD",
                "raw_evidence": (
                    "No direct support was "
                    "observed."
                ),
                "withheld_reason": (
                    "NOT_OBSERVED"
                ),
            },
        },
    }


class TestHoldoutV2ExpansionScorer(
    unittest.TestCase
):
    def test_default_paths_use_expansion_cohort(self):
        args = build_parser().parse_args([])

        self.assertEqual(
            args.cases_dir,
            DEFAULT_CASES_DIR,
        )
        self.assertEqual(
            args.annotations_dir,
            DEFAULT_ANNOTATIONS_DIR,
        )
        self.assertEqual(
            DEFAULT_CASES_DIR,
            Path(
                "benchmark/"
                "holdout_v2_expansion/cases"
            ),
        )

    def test_empty_expansion_cohort_is_rejected(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCORER),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        self.assertNotEqual(
            result.returncode,
            0,
        )
        self.assertIn(
            "no Holdout v2 cases found",
            result.stderr,
        )

    def test_frozen_holdout_directories_are_rejected(self):
        with self.assertRaisesRegex(
            ScoringError,
            "cannot read the frozen Holdout v2",
        ):
            run(
                cases_dir=Path(
                    "benchmark/holdout_v2/cases"
                ),
                annotations_dir=Path(
                    "benchmark/"
                    "holdout_v2/annotations"
                ),
            )

    def test_scores_isolated_expansion_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases_dir = root / "cases"
            annotations_dir = root / "annotations"

            cases_dir.mkdir()
            annotations_dir.mkdir()

            write_json(
                cases_dir / "expansion_001.json",
                make_case(),
            )
            write_json(
                (
                    annotations_dir
                    / "expansion_001.json"
                ),
                make_annotation(),
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCORER),
                    "--cases-dir",
                    str(cases_dir),
                    "--annotations-dir",
                    str(annotations_dir),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
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
            "HIGH",
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
            "Total WITHHELD:        1",
            result.stdout,
        )
        self.assertIn(
            "Reason specified:      1",
            result.stdout,
        )
        self.assertIn(
            "NOT_OBSERVED: 1",
            result.stdout,
        )


if __name__ == "__main__":
    unittest.main()
