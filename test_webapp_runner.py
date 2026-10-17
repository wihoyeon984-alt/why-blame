import json
import subprocess
import unittest
from unittest.mock import MagicMock, patch

from webapp.runner import (
    CLI_PATH,
    AnalysisResult,
    DashboardRunError,
    build_target,
    run_analysis,
)


class WebappRunnerTests(unittest.TestCase):
    def make_result(
        self,
        document,
        returncode=0,
        stderr=b"",
    ):
        result = MagicMock()
        result.returncode = returncode
        result.stdout = json.dumps(
            document,
            ensure_ascii=True,
        ).encode("ascii")
        result.stderr = stderr
        return result

    def test_build_target_for_single_line(self):
        self.assertEqual(
            build_target("src/service.py", 10, 10),
            "src/service.py:10",
        )

    def test_build_target_for_line_range(self):
        self.assertEqual(
            build_target("src/service.py", 10, 15),
            "src/service.py:10-15",
        )


    @patch("webapp.runner.subprocess.run")
    def test_run_analysis_parses_success_json(
        self,
        mock_run,
    ):
        document = {
            "schema_version": "1",
            "target": {
                "file": "src/service.py",
                "start_line": 10,
                "end_line": 10,
            },
            "repository": None,
            "current_lines": ["return True"],
            "timeline": [],
            "stats": {"confidence": "HIGH"},
        }

        mock_run.return_value = self.make_result(
            document
        )

        result = run_analysis(
            ".",
            "src/service.py",
            10,
            10,
        )

        self.assertIsInstance(
            result,
            AnalysisResult,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.document, document)

        command = mock_run.call_args.args[0]

        self.assertEqual(command[1], str(CLI_PATH))
        self.assertEqual(
            command[2],
            "src/service.py:10",
        )
        self.assertEqual(command[3], "--json")
        self.assertNotIn(
            "shell",
            mock_run.call_args.kwargs,
        )


    @patch("webapp.runner.subprocess.run")
    def test_run_analysis_preserves_error_json(
        self,
        mock_run,
    ):
        document = {
            "schema_version": "1",
            "error": {
                "code": "FILE_NOT_FOUND",
                "message": "File was not found.",
            },
        }

        mock_run.return_value = self.make_result(
            document,
            returncode=1,
        )

        result = run_analysis(
            ".",
            "missing.py",
            1,
            1,
        )

        self.assertIsInstance(
            result,
            AnalysisResult,
        )
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(
            result.document,
            document,
        )
        self.assertEqual(
            result.document["error"]["code"],
            "FILE_NOT_FOUND",
        )


    @patch("webapp.runner.subprocess.run")
    def test_run_analysis_rejects_stderr(
        self,
        mock_run,
    ):
        document = {
            "schema_version": "1",
            "error": {
                "code": "GIT_COMMAND_FAILED",
                "message": "Git failed.",
            },
        }

        mock_run.return_value = self.make_result(
            document,
            returncode=1,
            stderr=b"unexpected warning",
        )

        with self.assertRaisesRegex(
            DashboardRunError,
            "stderr",
        ):
            run_analysis(
                ".",
                "service.py",
                1,
                1,
            )


    @patch("webapp.runner.subprocess.run")
    def test_run_analysis_rejects_invalid_json(self, mock_run):
        result = MagicMock()
        result.returncode = 1
        result.stdout = b"not-json"
        result.stderr = b""
        mock_run.return_value = result

        with self.assertRaisesRegex(
            DashboardRunError,
            "valid JSON",
        ):
            run_analysis(
                ".",
                "service.py",
                1,
                1,
            )


    @patch("webapp.runner.subprocess.run")
    def test_run_analysis_rejects_unknown_schema(self, mock_run):
        mock_run.return_value = self.make_result(
            {
                "schema_version": "2",
                "target": {},
            }
        )

        with self.assertRaisesRegex(
            DashboardRunError,
            "Unsupported",
        ):
            run_analysis(
                ".",
                "service.py",
                1,
                1,
            )


    @patch("webapp.runner.subprocess.run")
    def test_run_analysis_converts_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["why-blame"],
            timeout=1,
        )

        with self.assertRaisesRegex(
            DashboardRunError,
            "timed out",
        ):
            run_analysis(
                ".",
                "service.py",
                1,
                1,
                timeout=1,
            )


    @patch("webapp.runner.subprocess.run")
    def test_run_analysis_converts_os_error(self, mock_run):
        mock_run.side_effect = OSError(
            "Unable to start process"
        )

        with self.assertRaisesRegex(
            DashboardRunError,
            "could not be started",
        ):
            run_analysis(
                ".",
                "service.py",
                1,
                1,
            )

        mock_run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
