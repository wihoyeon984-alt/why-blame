import copy
import json
import tempfile
import unittest
from pathlib import Path

from benchmark.holdout_v2.candidate import (
    CandidateError,
    load_candidate,
)


def make_candidate():
    return {
        "schema_version": 2,
        "candidate_id": "project_001",
        "repository": {
            "url": (
                "https://github.com/"
                "owner/project.git"
            ),
            "commit": "a" * 40,
        },
        "target": {
            "file": "src/module.py",
            "start_line": 10,
            "end_line": 24,
        },
        "status": "PROPOSED",
        "selection": {
            "rationale": (
                "Evaluate direct behavior and "
                "unsupported causal claims."
            ),
            "proposed_at": "2026-10-12",
            "proposed_by": "Wi Ho-yeon",
        },
        "exclusion": {
            "code": "",
            "reason": "",
        },
        "integrity": {
            "overlaps_holdout_v1": False,
            "overlap_details": "",
            "ground_truth_frozen": False,
            "system_executed": False,
            "annotation_complete": False,
        },
        "artifacts": {
            "case_file": "",
            "result_file": "",
            "annotation_file": "",
        },
        "notes": "",
    }


class TestHoldoutV2Candidate(unittest.TestCase):

    def load_data(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.json"

            path.write_text(
                json.dumps(data),
                encoding="utf-8",
            )

            return load_candidate(path)

    def test_loads_valid_proposed_candidate(self):
        candidate = self.load_data(
            make_candidate()
        )

        self.assertEqual(
            candidate.candidate_id,
            "project_001",
        )
        self.assertEqual(
            candidate.status,
            "PROPOSED",
        )
        self.assertEqual(
            candidate.target.start_line,
            10,
        )
        self.assertFalse(
            candidate.integrity.system_executed
        )

    def test_template_is_valid(self):
        candidate = load_candidate(
            Path(
                "benchmark/holdout_v2/"
                "candidates/"
                "CANDIDATE_TEMPLATE.json"
            )
        )

        self.assertEqual(
            candidate.schema_version,
            2,
        )
        self.assertEqual(
            candidate.status,
            "PROPOSED",
        )

    def test_rejects_invalid_candidate_id(self):
        data = make_candidate()
        data["candidate_id"] = "Project 001"

        with self.assertRaises(CandidateError):
            self.load_data(data)

    def test_rejects_invalid_commit_sha(self):
        data = make_candidate()
        data["repository"]["commit"] = "abc123"

        with self.assertRaises(CandidateError):
            self.load_data(data)

    def test_rejects_parent_target_path(self):
        data = make_candidate()
        data["target"]["file"] = "../secret.py"

        with self.assertRaises(CandidateError):
            self.load_data(data)

    def test_rejects_reversed_line_range(self):
        data = make_candidate()
        data["target"]["start_line"] = 30
        data["target"]["end_line"] = 10

        with self.assertRaises(CandidateError):
            self.load_data(data)

    def test_excluded_candidate_requires_reason(self):
        data = make_candidate()
        data["status"] = "EXCLUDED"
        data["exclusion"]["code"] = (
            "TARGET_NOT_FOUND"
        )

        with self.assertRaises(CandidateError):
            self.load_data(data)

    def test_frozen_candidate_requires_frozen_ground_truth(self):
        data = make_candidate()
        data["status"] = "FROZEN"
        data["artifacts"]["case_file"] = (
            "benchmark/holdout_v2/"
            "cases/project_001.json"
        )

        with self.assertRaises(CandidateError):
            self.load_data(data)

    def test_executed_candidate_requires_result(self):
        data = make_candidate()
        data["status"] = "EXECUTED"
        data["integrity"][
            "ground_truth_frozen"
        ] = True
        data["integrity"][
            "system_executed"
        ] = True
        data["artifacts"]["case_file"] = (
            "benchmark/holdout_v2/"
            "cases/project_001.json"
        )

        with self.assertRaises(CandidateError):
            self.load_data(data)

    def test_loads_valid_annotated_candidate(self):
        data = make_candidate()
        data["status"] = "ANNOTATED"
        data["integrity"][
            "ground_truth_frozen"
        ] = True
        data["integrity"][
            "system_executed"
        ] = True
        data["integrity"][
            "annotation_complete"
        ] = True
        data["artifacts"] = {
            "case_file": (
                "benchmark/holdout_v2/"
                "cases/project_001.json"
            ),
            "result_file": (
                "benchmark/holdout_v2/"
                "results/project_001.txt"
            ),
            "annotation_file": (
                "benchmark/holdout_v2/"
                "scoring/project_001.json"
            ),
        }

        candidate = self.load_data(data)

        self.assertEqual(
            candidate.status,
            "ANNOTATED",
        )
        self.assertTrue(
            candidate.integrity.annotation_complete
        )


if __name__ == "__main__":
    unittest.main()
