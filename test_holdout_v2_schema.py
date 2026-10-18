import json
import tempfile
import unittest
from pathlib import Path

from benchmark.holdout_v2.annotation import (
    VALID_WITHHELD_REASONS,
    load_annotation,
)


class TestHoldoutV2Schema(unittest.TestCase):

    def test_scoring_template_has_required_fields(self):
        path = Path(
            "benchmark/holdout_v2/"
            "SCORING_TEMPLATE.json"
        )

        data = json.loads(
            path.read_text(encoding="utf-8")
        )

        self.assertEqual(
            data["schema_version"],
            2,
        )
        self.assertIsInstance(
            data["case_id"],
            str,
        )
        self.assertIn(
            "completed",
            data["execution"],
        )
        self.assertIn(
            "level",
            data["confidence"],
        )
        self.assertIn(
            "source",
            data["confidence"],
        )
        self.assertIsInstance(
            data["claims"],
            dict,
        )


    def test_scoring_template_loads_as_annotation(self):
        source = Path(
            "benchmark/holdout_v2/"
            "SCORING_TEMPLATE.json"
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "annotation.json"
            path.write_text(
                source.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            annotation = load_annotation(path)

        self.assertEqual(
            annotation.schema_version,
            2,
        )
        self.assertEqual(
            annotation.claims[
                "claim_001"
            ].status,
            "PRESENTED",
        )
        self.assertEqual(
            annotation.claims[
                "claim_002"
            ].status,
            "WITHHELD",
        )
        self.assertEqual(
            annotation.claims[
                "claim_002"
            ].withheld_reason,
            "NOT_OBSERVED",
        )

    def test_scoring_template_uses_valid_withheld_reason(self):
        path = Path(
            "benchmark/holdout_v2/"
            "SCORING_TEMPLATE.json"
        )
        data = json.loads(
            path.read_text(encoding="utf-8")
        )

        reason = data["claims"]["claim_002"][
            "withheld_reason"
        ]

        self.assertIn(
            reason,
            VALID_WITHHELD_REASONS,
        )

    def test_readme_documents_withheld_reason_safety(self):
        text = Path(
            "benchmark/holdout_v2/README.md"
        ).read_text(encoding="utf-8")

        required = (
            "INSUFFICIENT_EVIDENCE",
            "CONFLICTING_EVIDENCE",
            "NOT_OBSERVED",
            "OUTSIDE_SUPPORTED_SCOPE",
            (
                "This does not mean that the claim is "
                "false or `UNSUPPORTED`."
            ),
            (
                "Do not derive `withheld_reason` from "
                "the Ground Truth label."
            ),
        )

        for fragment in required:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)


if __name__ == "__main__":
    unittest.main()
