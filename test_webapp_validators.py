import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from webapp.validators import (
    ValidatedTarget,
    ValidationError,
    validate_target,
)


class WebappValidatorTests(unittest.TestCase):
    def test_validate_target_accepts_safe_relative_file(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory).resolve()
            source = repository / "src" / "service.py"
            source.parent.mkdir()
            source.write_text(
                "def example():\n"
                "    return True\n",
                encoding="utf-8",
            )

            with patch(
                "webapp.validators.is_git_repository",
                return_value=True,
            ):
                result = validate_target(
                    repository,
                    "src/service.py",
                    1,
                    2,
                )

        self.assertIsInstance(
            result,
            ValidatedTarget,
        )
        self.assertEqual(
            result.repository,
            repository,
        )
        self.assertEqual(
            result.relative_file,
            "src/service.py",
        )
        self.assertEqual(result.start_line, 1)
        self.assertEqual(result.end_line, 2)


    def test_validate_target_rejects_parent_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve()
            repository = workspace / "repository"
            repository.mkdir()

            outside_file = workspace / "outside.py"
            outside_file.write_text(
                "print('outside')\n",
                encoding="utf-8",
            )

            with patch(
                "webapp.validators.is_git_repository",
                return_value=True,
            ):
                with self.assertRaisesRegex(
                    ValidationError,
                    "inside the repository",
                ):
                    validate_target(
                        repository,
                        "../outside.py",
                        1,
                        1,
                    )

    def test_validate_target_rejects_absolute_file(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory).resolve()
            source = repository / "service.py"
            source.write_text(
                "return_value = True\n",
                encoding="utf-8",
            )

            with patch(
                "webapp.validators.is_git_repository",
                return_value=True,
            ):
                with self.assertRaisesRegex(
                    ValidationError,
                    "must be relative",
                ):
                    validate_target(
                        repository,
                        source.resolve(),
                        1,
                        1,
                    )


    def test_validate_target_rejects_missing_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = (
                Path(directory)
                / "missing-repository"
            )

            with self.assertRaisesRegex(
                ValidationError,
                "existing directory",
            ):
                validate_target(
                    missing,
                    "service.py",
                    1,
                    1,
                )

    def test_validate_target_rejects_non_git_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory).resolve()

            with patch(
                "webapp.validators.is_git_repository",
                return_value=False,
            ):
                with self.assertRaisesRegex(
                    ValidationError,
                    "Git work tree",
                ):
                    validate_target(
                        repository,
                        "service.py",
                        1,
                        1,
                    )


    def test_validate_target_rejects_empty_file_path(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory).resolve()

            with patch(
                "webapp.validators.is_git_repository",
                return_value=True,
            ):
                with self.assertRaisesRegex(
                    ValidationError,
                    "file path is required",
                ):
                    validate_target(
                        repository,
                        "   ",
                        1,
                        1,
                    )

    def test_validate_target_rejects_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory).resolve()

            with patch(
                "webapp.validators.is_git_repository",
                return_value=True,
            ):
                with self.assertRaisesRegex(
                    ValidationError,
                    "does not exist",
                ):
                    validate_target(
                        repository,
                        "missing.py",
                        1,
                        1,
                    )


    def test_validate_target_rejects_nonpositive_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory).resolve()
            source = repository / "service.py"
            source.write_text(
                "return_value = True\n",
                encoding="utf-8",
            )

            with patch(
                "webapp.validators.is_git_repository",
                return_value=True,
            ):
                for start_line, end_line in [
                    (0, 1),
                    (1, 0),
                    (-1, 1),
                    (1, -1),
                ]:
                    with self.subTest(
                        start_line=start_line,
                        end_line=end_line,
                    ):
                        with self.assertRaisesRegex(
                            ValidationError,
                            "at least 1",
                        ):
                            validate_target(
                                repository,
                                "service.py",
                                start_line,
                                end_line,
                            )

    def test_validate_target_rejects_reversed_range(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory).resolve()
            source = repository / "service.py"
            source.write_text(
                "line one\n"
                "line two\n",
                encoding="utf-8",
            )

            with patch(
                "webapp.validators.is_git_repository",
                return_value=True,
            ):
                with self.assertRaisesRegex(
                    ValidationError,
                    "cannot exceed",
                ):
                    validate_target(
                        repository,
                        "service.py",
                        2,
                        1,
                    )

    def test_validate_target_rejects_noninteger_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory).resolve()
            source = repository / "service.py"
            source.write_text(
                "return_value = True\n",
                encoding="utf-8",
            )

            invalid_cases = [
                ("1", 1),
                (1, "1"),
                (1.0, 1),
                (1, 1.0),
                (True, 1),
                (1, False),
            ]

            with patch(
                "webapp.validators.is_git_repository",
                return_value=True,
            ):
                for start_line, end_line in invalid_cases:
                    with self.subTest(
                        start_line=start_line,
                        end_line=end_line,
                    ):
                        with self.assertRaisesRegex(
                            ValidationError,
                            "must be an integer",
                        ):
                            validate_target(
                                repository,
                                "service.py",
                                start_line,
                                end_line,
                            )


if __name__ == "__main__":
    unittest.main()
