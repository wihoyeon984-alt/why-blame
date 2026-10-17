import io
import json
import unittest
from contextlib import redirect_stdout

from json_renderer import (
    SCHEMA_VERSION,
    build_json_document,
    build_json_error_document,
    render_json,
    render_json_error,
)
from timeline import ConfidenceReport


KOREAN_CODE = "\ud55c\uae00 \ucf54\ub4dc"
KOREAN_MESSAGE = "\uccab \ubcc0\uacbd"
FIRST_OBSERVED = "\U0001f331 FIRST OBSERVED"


class JsonRendererTests(unittest.TestCase):
    def make_stats(self):
        report = ConfidenceReport(
            availability="MODERATE",
            consistency="HIGH",
            source_reliability="HIGH",
            history_ambiguity="LOW",
            overall_confidence="HIGH",
        )

        return {
            "score": 7,
            "confidence": "HIGH",
            "limitations": [],
            "report": report,
        }

    def test_build_json_document_preserves_structure(self):
        document = build_json_document(
            "service.py",
            10,
            12,
            ("owner", "repository"),
            ["line one", "line two"],
            [
                {
                    "hash": "abcdef123456",
                    "message": "Add behavior",
                    "diff_lines": ["+example"],
                    "ref_items": [],
                }
            ],
            self.make_stats(),
        )

        self.assertEqual(
            document["schema_version"],
            SCHEMA_VERSION,
        )
        self.assertEqual(
            document["target"],
            {
                "file": "service.py",
                "start_line": 10,
                "end_line": 12,
            },
        )
        self.assertEqual(
            document["repository"],
            {
                "owner": "owner",
                "name": "repository",
            },
        )
        self.assertEqual(
            document["current_lines"],
            ["line one", "line two"],
        )
        self.assertEqual(
            document["stats"]["report"][
                "overall_confidence"
            ],
            "HIGH",
        )

    def test_build_json_document_allows_missing_repository(self):
        document = build_json_document(
            "service.py",
            10,
            10,
            None,
            [],
            [],
            self.make_stats(),
        )

        self.assertIsNone(
            document["repository"]
        )

    def test_render_json_is_ascii_safe_and_preserves_unicode(self):
        output = io.StringIO()

        with redirect_stdout(output):
            render_json(
                "service.py",
                2,
                2,
                ("owner", "repository"),
                [KOREAN_CODE],
                [
                    {
                        "type": FIRST_OBSERVED,
                        "message": KOREAN_MESSAGE,
                    }
                ],
                self.make_stats(),
            )

        raw_output = output.getvalue()

        raw_output.encode("ascii")

        self.assertIn(
            "\\ud55c\\uae00",
            raw_output,
        )
        self.assertIn(
            "\\ud83c\\udf31",
            raw_output,
        )

        document = json.loads(raw_output)

        self.assertEqual(
            document["timeline"][0]["type"],
            FIRST_OBSERVED,
        )
        self.assertEqual(
            document["timeline"][0]["message"],
            KOREAN_MESSAGE,
        )
        self.assertEqual(
            document["current_lines"],
            [KOREAN_CODE],
        )

    def test_render_json_prints_one_parseable_document(self):
        output = io.StringIO()

        with redirect_stdout(output):
            render_json(
                "service.py",
                10,
                10,
                ("owner", "repository"),
                [KOREAN_CODE],
                [],
                self.make_stats(),
            )

        raw_output = output.getvalue()
        document = json.loads(raw_output)

        self.assertEqual(
            document["schema_version"],
            "1",
        )
        self.assertEqual(
            document["target"]["file"],
            "service.py",
        )
        self.assertEqual(
            document["current_lines"],
            [KOREAN_CODE],
        )

        raw_output.encode("ascii")

        self.assertIn(
            "\\ud55c\\uae00",
            raw_output,
        )


    def test_build_json_error_document(self):
        document = build_json_error_document(
            "INVALID_ARGUMENTS",
            "Missing target",
        )

        self.assertEqual(
            document,
            {
                "schema_version": "1",
                "error": {
                    "code": "INVALID_ARGUMENTS",
                    "message": "Missing target",
                },
            },
        )

    def test_render_json_error_is_ascii_safe(self):
        output = io.StringIO()

        with redirect_stdout(output):
            render_json_error(
                "INVALID_ARGUMENTS",
                "\ud55c\uae00 \uc624\ub958",
            )

        raw_output = output.getvalue()
        raw_output.encode("ascii")

        document = json.loads(raw_output)

        self.assertEqual(
            document["schema_version"],
            "1",
        )
        self.assertEqual(
            document["error"]["code"],
            "INVALID_ARGUMENTS",
        )
        self.assertEqual(
            document["error"]["message"],
            "\ud55c\uae00 \uc624\ub958",
        )


if __name__ == "__main__":
    unittest.main()
