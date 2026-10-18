import json
import tempfile
import unittest
from pathlib import Path

from benchmark.holdout_v2.annotation import (
    AnnotationError,
    load_annotation,
)


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
        },
    }


class TestHoldoutV2Annotation(unittest.TestCase):

    def load_data(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "annotation.json"

            path.write_text(
                json.dumps(data),
                encoding="utf-8",
            )

            return load_annotation(path)

    def test_loads_valid_annotation(self):
        annotation = self.load_data(
            make_annotation()
        )

        self.assertEqual(
            annotation.schema_version,
            2,
        )
        self.assertEqual(
            annotation.case_id,
            "example_001",
        )
        self.assertEqual(
            annotation.confidence_level,
            "VERY_HIGH",
        )
        self.assertEqual(
            annotation.confidence_source,
            "final_output",
        )
        self.assertEqual(
            annotation.claims[
                "claim_001"
            ].status,
            "PRESENTED",
        )

    def test_rejects_wrong_schema_version(self):
        data = make_annotation()
        data["schema_version"] = 1

        with self.assertRaises(
            AnnotationError
        ):
            self.load_data(data)

    def test_rejects_invalid_confidence(self):
        data = make_annotation()
        data["confidence"]["level"] = "VERY"

        with self.assertRaises(
            AnnotationError
        ):
            self.load_data(data)

    def test_normalizes_display_confidence(self):
        data = make_annotation()
        data["confidence"]["level"] = "VERY HIGH"

        annotation = self.load_data(data)

        self.assertEqual(
            annotation.confidence_level,
            "VERY_HIGH",
        )

    def test_rejects_invalid_claim_status(self):
        data = make_annotation()
        data["claims"]["claim_001"][
            "status"
        ] = "VISIBLE"

        with self.assertRaises(
            AnnotationError
        ):
            self.load_data(data)

    def test_rejects_missing_claims_object(self):
        data = make_annotation()
        del data["claims"]

        with self.assertRaises(
            AnnotationError
        ):
            self.load_data(data)


    def test_withheld_reason_is_optional_for_existing_annotations(self):
        data = make_annotation()
        data["claims"]["claim_001"]["status"] = "WITHHELD"

        annotation = self.load_data(data)

        self.assertEqual(
            annotation.claims["claim_001"].withheld_reason,
            "",
        )

    def test_loads_valid_withheld_reason(self):
        data = make_annotation()
        data["claims"]["claim_001"]["status"] = "WITHHELD"
        data["claims"]["claim_001"]["withheld_reason"] = (
            "INSUFFICIENT_EVIDENCE"
        )

        annotation = self.load_data(data)

        self.assertEqual(
            annotation.claims["claim_001"].withheld_reason,
            "INSUFFICIENT_EVIDENCE",
        )

    def test_rejects_unknown_withheld_reason(self):
        data = make_annotation()
        data["claims"]["claim_001"]["status"] = "WITHHELD"
        data["claims"]["claim_001"]["withheld_reason"] = (
            "UNKNOWN_REASON"
        )

        with self.assertRaisesRegex(
            AnnotationError,
            "invalid withheld_reason",
        ):
            self.load_data(data)

    def test_rejects_empty_withheld_reason(self):
        data = make_annotation()
        data["claims"]["claim_001"]["status"] = "WITHHELD"
        data["claims"]["claim_001"]["withheld_reason"] = ""

        with self.assertRaisesRegex(
            AnnotationError,
            "must be a non-empty string",
        ):
            self.load_data(data)

    def test_rejects_withheld_reason_for_presented_claim(self):
        data = make_annotation()
        data["claims"]["claim_001"]["withheld_reason"] = (
            "NOT_OBSERVED"
        )

        with self.assertRaisesRegex(
            AnnotationError,
            "requires WITHHELD status",
        ):
            self.load_data(data)


if __name__ == "__main__":
    unittest.main()
