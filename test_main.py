import io
import json
import unittest
from contextlib import ExitStack
from unittest.mock import patch

import main


class MainCliTests(unittest.TestCase):
    def run_main(self, arguments):
        output = io.StringIO()

        argv_patch = patch.object(
            main.sys,
            "argv",
            ["why-blame"] + arguments,
        )
        stdout_patch = patch(
            "sys.stdout",
            output,
        )

        with argv_patch:
            with stdout_patch:
                main.main()

        return output.getvalue()

    def test_long_version_option(self):
        version_patch = patch.object(
            main,
            "get_version",
            return_value="1.2.3",
        )

        with version_patch:
            output = self.run_main(
                ["--version"]
            )

        self.assertEqual(
            output,
            "why-blame 1.2.3\n",
        )

    def test_short_version_option(self):
        version_patch = patch.object(
            main,
            "get_version",
            return_value="1.2.3",
        )

        with version_patch:
            output = self.run_main(["-V"])

        self.assertEqual(
            output,
            "why-blame 1.2.3\n",
        )

    def test_get_version_uses_local_pyproject(self):
        pyproject_text = (
            '[project]\n'
            'name = "why-blame"\n'
            'version = "9.8.7"\n'
        )

        file_patch = patch.object(
            main.Path,
            "is_file",
            return_value=True,
        )
        read_patch = patch.object(
            main.Path,
            "read_text",
            return_value=pyproject_text,
        )
        metadata_patch = patch.object(
            main,
            "version",
        )

        with file_patch:
            with read_patch:
                with metadata_patch as mocked_version:
                    result = main.get_version()

        self.assertEqual(result, "9.8.7")
        mocked_version.assert_not_called()

    def test_get_version_uses_package_metadata(self):
        file_patch = patch.object(
            main.Path,
            "is_file",
            return_value=False,
        )
        metadata_patch = patch.object(
            main,
            "version",
            return_value="0.3.4",
        )

        with file_patch:
            with metadata_patch as mocked_version:
                result = main.get_version()

        self.assertEqual(result, "0.3.4")
        mocked_version.assert_called_once_with(
            "why-blame"
        )

    def test_get_version_falls_back_when_not_installed(self):
        file_patch = patch.object(
            main.Path,
            "is_file",
            return_value=False,
        )
        metadata_patch = patch.object(
            main,
            "version",
            side_effect=main.PackageNotFoundError,
        )

        with file_patch:
            with metadata_patch:
                result = main.get_version()

        self.assertEqual(result, "unknown")


    def test_parse_output_mode_accepts_json_after_target(self):
        arguments, json_output = main.parse_output_mode(
            ["service.py:10", "--json"]
        )

        self.assertEqual(
            arguments,
            ["service.py:10"],
        )
        self.assertTrue(json_output)

    def test_parse_output_mode_accepts_json_before_target(self):
        arguments, json_output = main.parse_output_mode(
            ["--json", "service.py:10"]
        )

        self.assertEqual(
            arguments,
            ["service.py:10"],
        )
        self.assertTrue(json_output)

    def test_parse_output_mode_rejects_duplicate_json(self):
        with self.assertRaises(ValueError):
            main.parse_output_mode(
                [
                    "--json",
                    "service.py:10",
                    "--json",
                ]
            )

    def test_parse_output_mode_rejects_version_combination(self):
        with self.assertRaises(ValueError):
            main.parse_output_mode(
                ["--version", "--json"]
            )

    def test_json_mode_uses_json_renderer_only(self):
        current_lines = ["example"]
        timeline = [
            {
                "hash": "abcdef123456",
                "message": "Add example",
            }
        ]
        stats = {
            "score": 3,
            "confidence": "HIGH",
        }

        patches = [
            patch.object(
                main,
                "get_file_line_count",
                return_value=100,
            ),
            patch.object(
                main,
                "get_current_code_lines",
                return_value=current_lines,
            ),
            patch.object(
                main,
                "get_repo_info",
                return_value=("owner", "repo"),
            ),
            patch.object(
                main,
                "extract_git_history",
                return_value=[{"hash": "abcdef123456"}],
            ),
            patch.object(
                main,
                "build_timeline",
                return_value=(timeline, stats),
            ),
            patch.object(
                main,
                "render_json",
            ),
            patch.object(
                main,
                "render_card",
            ),
        ]

        with ExitStack() as stack:
            for patcher in patches[:5]:
                stack.enter_context(patcher)

            mocked_json = stack.enter_context(
                patches[5]
            )
            mocked_card = stack.enter_context(
                patches[6]
            )

            self.run_main(
                [
                    "service.py:10",
                    "--json",
                ]
            )

        mocked_json.assert_called_once_with(
            "service.py",
            10,
            10,
            ("owner", "repo"),
            current_lines,
            timeline,
            stats,
        )
        mocked_card.assert_not_called()

    def test_default_mode_keeps_card_renderer(self):
        current_lines = ["example"]
        timeline = [
            {
                "hash": "abcdef123456",
                "message": "Add example",
            }
        ]
        stats = {
            "score": 3,
            "confidence": "HIGH",
        }

        patches = [
            patch.object(
                main,
                "get_file_line_count",
                return_value=100,
            ),
            patch.object(
                main,
                "get_current_code_lines",
                return_value=current_lines,
            ),
            patch.object(
                main,
                "get_repo_info",
                return_value=("owner", "repo"),
            ),
            patch.object(
                main,
                "extract_git_history",
                return_value=[{"hash": "abcdef123456"}],
            ),
            patch.object(
                main,
                "build_timeline",
                return_value=(timeline, stats),
            ),
            patch.object(
                main,
                "render_json",
            ),
            patch.object(
                main,
                "render_card",
            ),
        ]

        with ExitStack() as stack:
            for patcher in patches[:5]:
                stack.enter_context(patcher)

            mocked_json = stack.enter_context(
                patches[5]
            )
            mocked_card = stack.enter_context(
                patches[6]
            )

            self.run_main(
                ["service.py:10"]
            )

        mocked_card.assert_called_once_with(
            "service.py",
            "10",
            ("owner", "repo"),
            current_lines,
            timeline,
            stats,
        )
        mocked_json.assert_not_called()


    def run_main_expecting_exit(
        self,
        arguments,
        expected_exit_code,
    ):
        output = io.StringIO()

        with patch.object(
            main.sys,
            "argv",
            ["why-blame"] + arguments,
        ):
            with patch(
                "sys.stdout",
                output,
            ):
                with self.assertRaises(
                    SystemExit
                ) as raised:
                    main.main()

        self.assertEqual(
            raised.exception.code,
            expected_exit_code,
        )

        return output.getvalue()

    def test_json_missing_target_returns_structured_error(self):
        output = self.run_main_expecting_exit(
            ["--json"],
            2,
        )

        document = json.loads(output)

        self.assertEqual(
            document["schema_version"],
            "1",
        )
        self.assertEqual(
            document["error"]["code"],
            "INVALID_ARGUMENTS",
        )
        self.assertNotIn(
            main.USAGE,
            output,
        )

    def test_duplicate_json_returns_structured_error(self):
        output = self.run_main_expecting_exit(
            [
                "--json",
                "service.py:10",
                "--json",
            ],
            2,
        )

        document = json.loads(output)

        self.assertEqual(
            document["error"]["code"],
            "INVALID_ARGUMENTS",
        )
        self.assertNotIn(
            main.USAGE,
            output,
        )

    def test_json_no_history_returns_structured_error(self):
        patches = [
            patch.object(
                main,
                "get_file_line_count",
                return_value=100,
            ),
            patch.object(
                main,
                "get_current_code_lines",
                return_value=["example"],
            ),
            patch.object(
                main,
                "get_repo_info",
                return_value=None,
            ),
            patch.object(
                main,
                "extract_git_history",
                return_value=[],
            ),
        ]

        with ExitStack() as stack:
            for patcher in patches:
                stack.enter_context(patcher)

            output = self.run_main_expecting_exit(
                [
                    "service.py:10",
                    "--json",
                ],
                1,
            )

        document = json.loads(output)

        self.assertEqual(
            document["schema_version"],
            "1",
        )
        self.assertEqual(
            document["error"]["code"],
            "NO_HISTORY",
        )

    def test_human_error_keeps_usage_output(self):
        with patch.object(
            main,
            "render_json_error",
        ) as mocked_json_error:
            output = self.run_main_expecting_exit(
                [],
                2,
            )

        self.assertIn(
            main.USAGE,
            output,
        )
        mocked_json_error.assert_not_called()


    def test_json_file_not_found_error(self):
        with patch.object(
            main.Path,
            "is_file",
            return_value=False,
        ):
            with patch.object(
                main,
                "is_git_repository",
            ) as mocked_git_check:
                output = self.run_main_expecting_exit(
                    [
                        "missing.py:1",
                        "--json",
                    ],
                    1,
                )

        document = json.loads(output)

        self.assertEqual(
            document["schema_version"],
            "1",
        )
        self.assertEqual(
            document["error"]["code"],
            "FILE_NOT_FOUND",
        )
        self.assertIn(
            "missing.py",
            document["error"]["message"],
        )
        mocked_git_check.assert_not_called()

    def test_json_not_a_git_repository_error(self):
        with patch.object(
            main.Path,
            "is_file",
            return_value=True,
        ):
            with patch.object(
                main,
                "is_git_repository",
                return_value=False,
            ):
                output = self.run_main_expecting_exit(
                    [
                        "service.py:2",
                        "--json",
                    ],
                    1,
                )

        document = json.loads(output)

        self.assertEqual(
            document["schema_version"],
            "1",
        )
        self.assertEqual(
            document["error"]["code"],
            "NOT_A_GIT_REPOSITORY",
        )

    def test_human_file_not_found_keeps_text_output(self):
        with patch.object(
            main.Path,
            "is_file",
            return_value=False,
        ):
            with patch.object(
                main,
                "render_json_error",
            ) as mocked_json_error:
                output = self.run_main_expecting_exit(
                    ["missing.py:1"],
                    1,
                )

        self.assertIn(
            "The requested file does not exist",
            output,
        )
        self.assertIn(
            "missing.py",
            output,
        )
        self.assertNotIn(
            '"schema_version"',
            output,
        )
        mocked_json_error.assert_not_called()

    def test_file_check_precedes_repository_check(self):
        with patch.object(
            main.Path,
            "is_file",
            return_value=False,
        ):
            with patch.object(
                main,
                "is_git_repository",
            ) as mocked_git_check:
                output = self.run_main_expecting_exit(
                    [
                        "missing.py:1",
                        "--json",
                    ],
                    1,
                )

        document = json.loads(output)

        self.assertEqual(
            document["error"]["code"],
            "FILE_NOT_FOUND",
        )
        mocked_git_check.assert_not_called()


    def test_json_single_line_out_of_bounds(self):
        with patch.object(
            main.Path,
            "is_file",
            return_value=True,
        ), patch.object(
            main,
            "get_file_line_count",
            return_value=3,
        ), patch.object(
            main,
            "is_git_repository",
        ) as mocked_git_check:
            output = self.run_main_expecting_exit(
                ["service.py:4", "--json"],
                1,
            )

        document = json.loads(output)

        self.assertEqual(
            document["error"]["code"],
            "LINE_RANGE_OUT_OF_BOUNDS",
        )
        self.assertIn(
            "4",
            document["error"]["message"],
        )
        self.assertIn(
            "3",
            document["error"]["message"],
        )
        mocked_git_check.assert_not_called()

    def test_json_range_end_out_of_bounds(self):
        with patch.object(
            main.Path,
            "is_file",
            return_value=True,
        ), patch.object(
            main,
            "get_file_line_count",
            return_value=3,
        ), patch.object(
            main,
            "is_git_repository",
        ) as mocked_git_check:
            output = self.run_main_expecting_exit(
                ["service.py:2-4", "--json"],
                1,
            )

        document = json.loads(output)

        self.assertEqual(
            document["schema_version"],
            "1",
        )
        self.assertEqual(
            document["error"]["code"],
            "LINE_RANGE_OUT_OF_BOUNDS",
        )
        self.assertIn(
            "2-4",
            document["error"]["message"],
        )
        mocked_git_check.assert_not_called()

    def test_json_empty_file_rejects_first_line(self):
        with patch.object(
            main.Path,
            "is_file",
            return_value=True,
        ), patch.object(
            main,
            "get_file_line_count",
            return_value=0,
        ), patch.object(
            main,
            "is_git_repository",
        ) as mocked_git_check:
            output = self.run_main_expecting_exit(
                ["empty.py:1", "--json"],
                1,
            )

        document = json.loads(output)

        self.assertEqual(
            document["error"]["code"],
            "LINE_RANGE_OUT_OF_BOUNDS",
        )
        self.assertIn(
            "file length of 0",
            document["error"]["message"],
        )
        mocked_git_check.assert_not_called()


    def test_human_line_range_out_of_bounds(self):
        with patch.object(
            main.Path,
            "is_file",
            return_value=True,
        ), patch.object(
            main,
            "get_file_line_count",
            return_value=3,
        ), patch.object(
            main,
            "render_json_error",
        ) as mocked_json_error:
            output = self.run_main_expecting_exit(
                ["service.py:4"],
                1,
            )

        self.assertIn(
            "The requested line range 4",
            output,
        )
        self.assertIn(
            "file length of 3",
            output,
        )
        self.assertNotIn(
            '"schema_version"',
            output,
        )
        mocked_json_error.assert_not_called()

    def test_last_valid_line_is_allowed(self):
        current_lines = ["last line"]
        timeline = [
            {
                "hash": "abcdef123456",
                "message": "Add last line",
            }
        ]
        stats = {
            "score": 3,
            "confidence": "HIGH",
        }

        patches = [
            patch.object(
                main.Path,
                "is_file",
                return_value=True,
            ),
            patch.object(
                main,
                "get_file_line_count",
                return_value=3,
            ),
            patch.object(
                main,
                "is_git_repository",
                return_value=True,
            ),
            patch.object(
                main,
                "get_current_code_lines",
                return_value=current_lines,
            ),
            patch.object(
                main,
                "get_repo_info",
                return_value=("owner", "repo"),
            ),
            patch.object(
                main,
                "extract_git_history",
                return_value=[
                    {"hash": "abcdef123456"}
                ],
            ),
            patch.object(
                main,
                "build_timeline",
                return_value=(timeline, stats),
            ),
            patch.object(
                main,
                "render_json",
            ),
            patch.object(
                main,
                "render_card",
            ),
        ]

        with ExitStack() as stack:
            for patcher in patches[:7]:
                stack.enter_context(patcher)

            mocked_json = stack.enter_context(
                patches[7]
            )
            mocked_card = stack.enter_context(
                patches[8]
            )

            self.run_main(
                ["service.py:3", "--json"]
            )

        mocked_json.assert_called_once_with(
            "service.py",
            3,
            3,
            ("owner", "repo"),
            current_lines,
            timeline,
            stats,
        )
        mocked_card.assert_not_called()


    def test_json_permission_error_returns_file_read_error(self):
        with patch.object(
            main.Path,
            "is_file",
            return_value=True,
        ), patch.object(
            main,
            "get_file_line_count",
            side_effect=PermissionError("Access denied"),
        ), patch.object(
            main,
            "is_git_repository",
        ) as mocked_git_check:
            output = self.run_main_expecting_exit(
                ["service.py:1", "--json"],
                1,
            )

        document = json.loads(output)

        self.assertEqual(
            document["error"]["code"],
            "FILE_READ_ERROR",
        )
        self.assertIn(
            "PermissionError",
            document["error"]["message"],
        )
        mocked_git_check.assert_not_called()

    def test_json_decode_error_returns_file_read_error(self):
        decode_error = UnicodeDecodeError(
            "utf-8",
            b"\xff",
            0,
            1,
            "invalid start byte",
        )

        with patch.object(
            main.Path,
            "is_file",
            return_value=True,
        ), patch.object(
            main,
            "get_file_line_count",
            side_effect=decode_error,
        ):
            output = self.run_main_expecting_exit(
                ["service.py:1", "--json"],
                1,
            )

        document = json.loads(output)

        self.assertEqual(
            document["schema_version"],
            "1",
        )
        self.assertEqual(
            document["error"]["code"],
            "FILE_READ_ERROR",
        )
        self.assertIn(
            "UnicodeDecodeError",
            document["error"]["message"],
        )


    def test_json_os_error_returns_file_read_error(self):
        with patch.object(
            main.Path,
            "is_file",
            return_value=True,
        ), patch.object(
            main,
            "get_file_line_count",
            side_effect=OSError("File system error"),
        ):
            output = self.run_main_expecting_exit(
                ["service.py:1", "--json"],
                1,
            )

        document = json.loads(output)

        self.assertEqual(
            document["error"]["code"],
            "FILE_READ_ERROR",
        )
        self.assertIn(
            "OSError",
            document["error"]["message"],
        )

    def test_file_removed_after_precheck_returns_file_not_found(self):
        with patch.object(
            main.Path,
            "is_file",
            return_value=True,
        ), patch.object(
            main,
            "get_file_line_count",
            side_effect=FileNotFoundError,
        ), patch.object(
            main,
            "is_git_repository",
        ) as mocked_git_check:
            output = self.run_main_expecting_exit(
                ["service.py:1", "--json"],
                1,
            )

        document = json.loads(output)

        self.assertEqual(
            document["error"]["code"],
            "FILE_NOT_FOUND",
        )
        mocked_git_check.assert_not_called()

    def test_human_file_read_error_keeps_text_output(self):
        with patch.object(
            main.Path,
            "is_file",
            return_value=True,
        ), patch.object(
            main,
            "get_file_line_count",
            side_effect=PermissionError("Access denied"),
        ), patch.object(
            main,
            "render_json_error",
        ) as mocked_json_error:
            output = self.run_main_expecting_exit(
                ["service.py:1"],
                1,
            )

        self.assertIn(
            "The requested file could not be read",
            output,
        )
        self.assertIn(
            "PermissionError",
            output,
        )
        self.assertNotIn(
            '"schema_version"',
            output,
        )
        mocked_json_error.assert_not_called()


if __name__ == "__main__":
    unittest.main()
