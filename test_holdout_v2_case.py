import json
import tempfile
import unittest
from pathlib import Path

from benchmark.holdout_v2.case import (
    CaseError,
    load_case,
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
            "commit": "abc123def456",
        },
        "frozen": True,
        "claims": {
            "claim_001": {
                "label": "SUPPORTED",
            },
            "claim_002": {
                "label": "UNSUPPORTED",
            },
        },
    }


class TestHoldoutV2Case(unittest.TestCase):

    def load_data(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "case.json"

            path.write_text(
                json.dumps(data),
                encoding="utf-8",
            )

            return load_case(path)

    def test_loads_valid_case(self):
        case = self.load_data(
            make_case()
        )

        self.assertEqual(
            case.schema_version,
            2,
        )
        self.assertEqual(
            case.case_id,
            "example_001",
        )
        self.assertEqual(
            case.repository_url,
            (
                "https://github.com/"
                "example/project.git"
            ),
        )
        self.assertEqual(
            case.repository_commit,
            "abc123def456",
        )
        self.assertTrue(case.frozen)
        self.assertEqual(
            case.claims["claim_001"].label,
            "SUPPORTED",
        )

    def test_rejects_wrong_schema_version(self):
        data = make_case()
        data["schema_version"] = 1

        with self.assertRaises(CaseError):
            self.load_data(data)

    def test_rejects_empty_case_id(self):
        data = make_case()
        data["case_id"] = ""

        with self.assertRaises(CaseError):
            self.load_data(data)

    def test_rejects_missing_repository(self):
        data = make_case()
        del data["repository"]

        with self.assertRaises(CaseError):
            self.load_data(data)

    def test_rejects_non_frozen_case(self):
        data = make_case()
        data["frozen"] = False

        with self.assertRaises(CaseError):
            self.load_data(data)

    def test_rejects_invalid_claim_label(self):
        data = make_case()
        data["claims"]["claim_001"][
            "label"
        ] = "PROBABLY_SUPPORTED"

        with self.assertRaises(CaseError):
            self.load_data(data)

    def test_rejects_missing_claims(self):
        data = make_case()
        del data["claims"]

        with self.assertRaises(CaseError):
            self.load_data(data)

    def test_rejects_empty_claims(self):
        data = make_case()
        data["claims"] = {}

        with self.assertRaises(CaseError):
            self.load_data(data)


if __name__ == "__main__":
    unittest.main()
