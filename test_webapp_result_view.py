import unittest

from webapp.result_view import (
    ErrorView,
    ResultViewError,
    SuccessView,
    build_result_view,
)


class WebappResultViewTests(unittest.TestCase):
    def make_success_document(self):
        return {
            "schema_version": "1",
            "target": {
                "file": "service.py",
                "start_line": 1,
                "end_line": 2,
            },
            "repository": None,
            "current_lines": [
                "def example():",
                "    return True",
            ],
            "timeline": [],
            "stats": {
                "confidence": "HIGH",
            },
        }

    def test_error_document_returns_error_view(self):
        view = build_result_view(
            {
                "schema_version": "1",
                "error": {
                    "code": "FILE_NOT_FOUND",
                    "message": "File not found.",
                },
            }
        )

        self.assertIsInstance(view, ErrorView)
        self.assertEqual(view.code, "FILE_NOT_FOUND")
        self.assertEqual(view.message, "File not found.")

    def test_success_document_returns_success_view(self):
        document = self.make_success_document()

        view = build_result_view(document)

        self.assertIsInstance(view, SuccessView)
        self.assertEqual(view.target, document["target"])
        self.assertEqual(
            view.current_lines,
            document["current_lines"],
        )
        self.assertEqual(view.timeline, [])
        self.assertEqual(
            view.stats["confidence"],
            "HIGH",
        )
        self.assertIsNone(view.beginner_evidence)

    def test_beginner_evidence_dict_is_preserved(self):
        document = self.make_success_document()
        document["beginner_evidence"] = {
            "reason_status": "title_only",
            "unknown_items": ["unrecorded_developer_intent"],
        }

        view = build_result_view(document)

        self.assertIs(
            view.beginner_evidence,
            document["beginner_evidence"],
        )

    def test_invalid_beginner_evidence_is_rejected(self):
        for value in ([], "invalid", 42):
            document = self.make_success_document()
            document["beginner_evidence"] = value

            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    ResultViewError,
                    "beginner evidence",
                ):
                    build_result_view(document)


    def test_rejects_unknown_schema(self):
        with self.assertRaisesRegex(
            ResultViewError,
            "Unsupported",
        ):
            build_result_view(
                {
                    "schema_version": "2",
                    "target": {},
                }
            )

    def test_rejects_invalid_error_document(self):
        with self.assertRaisesRegex(
            ResultViewError,
            "error code",
        ):
            build_result_view(
                {
                    "schema_version": "1",
                    "error": {
                        "code": "",
                        "message": "Missing code.",
                    },
                }
            )


if __name__ == "__main__":
    unittest.main()
