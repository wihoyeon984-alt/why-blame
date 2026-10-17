import importlib.util
import json
import unittest
from pathlib import Path


path = Path("scripts/check_release_install.py")
spec = importlib.util.spec_from_file_location(
    "check_release_install",
    path,
)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def make_output():
    document = {
        "schema_version": "1",
        "target": {
            "file": "service.py",
            "start_line": 2,
            "end_line": 2,
        },
        "repository": None,
        "current_lines": ["return user.is_active"],
        "timeline": [{"message": "Add sample service"}],
        "stats": {"confidence": "WEAK"},
    }
    return json.dumps(
        document,
        ensure_ascii=True,
    ).encode("ascii")


class ReleaseInstallCheckerTests(unittest.TestCase):
    def test_accepts_schema_v1(self):
        document = checker.validate_json_output(
            make_output(),
            b"",
            "service.py",
            2,
        )
        self.assertEqual(document["schema_version"], "1")

    def test_rejects_stderr(self):
        with self.assertRaises(ValueError):
            checker.validate_json_output(
                make_output(),
                b"warning",
                "service.py",
                2,
            )

    def test_rejects_wrong_schema(self):
        output = make_output().replace(
            b'"schema_version": "1"',
            b'"schema_version": "2"',
        )
        with self.assertRaises(ValueError):
            checker.validate_json_output(
                output,
                b"",
                "service.py",
                2,
            )

    def test_rejects_empty_timeline(self):
        output = make_output().replace(
            b'"timeline": [{"message": "Add sample service"}]',
            b'"timeline": []',
        )
        with self.assertRaises(ValueError):
            checker.validate_json_output(
                output,
                b"",
                "service.py",
                2,
            )


    def make_error_output(self, code="INVALID_ARGUMENTS"):
        document = {
            "schema_version": "1",
            "error": {
                "code": code,
                "message": "Missing target",
            },
        }

        return json.dumps(
            document,
            ensure_ascii=True,
        ).encode("ascii")

    def test_accepts_json_error_output(self):
        document = (
            checker.validate_json_error_output(
                self.make_error_output(),
                b"",
                2,
                2,
                "INVALID_ARGUMENTS",
            )
        )

        self.assertEqual(
            document["schema_version"],
            "1",
        )
        self.assertEqual(
            document["error"]["code"],
            "INVALID_ARGUMENTS",
        )

    def test_rejects_json_error_wrong_exit_code(self):
        with self.assertRaises(ValueError):
            checker.validate_json_error_output(
                self.make_error_output(),
                b"",
                1,
                2,
                "INVALID_ARGUMENTS",
            )

    def test_rejects_json_error_stderr(self):
        with self.assertRaises(ValueError):
            checker.validate_json_error_output(
                self.make_error_output(),
                b"warning",
                2,
                2,
                "INVALID_ARGUMENTS",
            )

    def test_rejects_json_error_wrong_code(self):
        with self.assertRaises(ValueError):
            checker.validate_json_error_output(
                self.make_error_output(
                    "NO_HISTORY"
                ),
                b"",
                2,
                2,
                "INVALID_ARGUMENTS",
            )


if __name__ == "__main__":
    unittest.main()
