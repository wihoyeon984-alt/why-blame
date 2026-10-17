import unittest

from webapp.result_view import (
    ErrorView,
    ResultViewError,
    SuccessView,
    build_result_view,
)


class WebappResultViewTests(unittest.TestCase):
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
        document = {
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
