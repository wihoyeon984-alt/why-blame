import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from benchmark.holdout.run_holdout import parse_execution_case, parse_preserved_target, resolve_preserved_target, read_preserved_output, discover_case_paths, prepare_repository, run_case, write_case_output, run_candidate_case, resolve_execution_case, main


class TestHoldoutRunner(unittest.TestCase):

    def test_parse_execution_case_reads_frozen_target(self):
        text = """
id: synthetic_001

repository:
  owner: "example"
  name: "project"
  url: "https://example.invalid/project"

revision:
  commit: "abc123"

target:
  file: "src/example.py"
  start_line: 10
  end_line: 12
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "synthetic_001.yaml"
            path.write_text(
                text,
                encoding="utf-8",
            )

            case = parse_execution_case(path)

        self.assertEqual(case.case_id, "synthetic_001")
        self.assertEqual(
            case.repository_url,
            "https://example.invalid/project",
        )
        self.assertEqual(case.commit, "abc123")
        self.assertEqual(case.target_file, "src/example.py")
        self.assertEqual(case.start_line, 10)
        self.assertEqual(case.end_line, 12)



    def test_parse_execution_case_rejects_placeholder_lines(self):
        text = """
id: synthetic_placeholder

repository:
  url: "https://example.invalid/project"

revision:
  commit: "abc123"

target:
  file: "src/example.py"
  start_line: START_LINE
  end_line: END_LINE
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "synthetic_placeholder.yaml"
            path.write_text(
                text,
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                parse_execution_case(path)


    def test_parse_preserved_target_reads_rendered_target(self):
        output = """
WHY-BLAME
TARGET: src/example.py:1620-1621
REPO: example/project
"""

        target_file, start_line, end_line = (
            parse_preserved_target(output)
        )

        self.assertEqual(
            target_file,
            "src/example.py",
        )
        self.assertEqual(
            start_line,
            1620,
        )
        self.assertEqual(
            end_line,
            1621,
        )


    def test_resolve_preserved_target_requires_matching_artifacts(self):
        first_output = """
WHY-BLAME
TARGET: src/example.py:1620-1621
REPO: example/project
"""

        current_output = """
WHY-BLAME
TARGET: src/example.py:1620-1621
REPO: example/project
"""

        result = resolve_preserved_target(
            first_output,
            current_output,
        )

        self.assertEqual(
            result,
            ("src/example.py", 1620, 1621),
        )


    def test_resolve_preserved_target_rejects_disagreement(self):
        first_output = """
WHY-BLAME
TARGET: src/example.py:1620-1621
"""

        current_output = """
WHY-BLAME
TARGET: src/example.py:1700-1701
"""

        with self.assertRaises(ValueError):
            resolve_preserved_target(
                first_output,
                current_output,
            )



    def test_real_black_execution_case_recovers_preserved_target(self):
        root = Path(__file__).resolve().parent
        holdout_dir = root / "benchmark" / "holdout"

        case = resolve_execution_case(
            holdout_dir / "cases" / "black_001.yaml",
            holdout_dir / "results" / "black_001.txt",
            holdout_dir / "current_run" / "black_001.txt",
        )

        self.assertEqual(
            case.case_id,
            "black_001",
        )
        self.assertEqual(
            case.target_file,
            "src/black/linegen.py",
        )
        self.assertEqual(
            case.start_line,
            1620,
        )
        self.assertEqual(
            case.end_line,
            1621,
        )
    def test_real_black_preserved_outputs_agree_on_target(self):
        root = Path(__file__).resolve().parent
        holdout_dir = root / "benchmark" / "holdout"

        first_output = read_preserved_output(
            holdout_dir / "results" / "black_001.txt"
        )

        current_output = read_preserved_output(
            holdout_dir / "current_run" / "black_001.txt"
        )

        result = resolve_preserved_target(
            first_output,
            current_output,
        )

        self.assertEqual(
            result,
            (
                "src/black/linegen.py",
                1620,
                1621,
            ),
        )


    def test_read_preserved_output_decodes_utf16_bom(self):
        text = (
            "WHY-BLAME\n"
            "TARGET: src/example.py:1620-1621\n"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "output.txt"
            path.write_text(
                text,
                encoding="utf-16",
            )

            result = read_preserved_output(path)

        self.assertEqual(
            result.splitlines(),
            text.splitlines(),
        )


    def test_real_holdout_discovers_ten_cases_without_template(self):
        root = Path(__file__).resolve().parent
        cases_dir = root / "benchmark" / "holdout" / "cases"

        paths = discover_case_paths(
            cases_dir
        )

        self.assertEqual(
            len(paths),
            10,
        )
        self.assertNotIn(
            "CASE_TEMPLATE.yaml",
            {path.name for path in paths},
        )


    @patch("benchmark.holdout.run_holdout.subprocess.run")
    def test_prepare_repository_clones_and_checks_out_frozen_commit(
        self,
        mock_run,
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "project"

            prepare_repository(
                "https://example.invalid/project.git",
                "abc123",
                destination,
            )

        self.assertEqual(
            mock_run.call_count,
            2,
        )

        clone_call = mock_run.call_args_list[0]
        checkout_call = mock_run.call_args_list[1]

        self.assertEqual(
            clone_call.args[0],
            [
                "git",
                "clone",
                "https://example.invalid/project.git",
                str(destination),
            ],
        )
        self.assertEqual(
            checkout_call.args[0],
            [
                "git",
                "-C",
                str(destination),
                "checkout",
                "--detach",
                "abc123",
            ],
        )


    @patch("benchmark.holdout.run_holdout.subprocess.run")
    def test_run_case_executes_why_blame_in_frozen_repository(
        self,
        mock_run,
    ):
        text = """
id: synthetic_run

repository:
  url: "https://example.invalid/project"

revision:
  commit: "abc123"

target:
  file: "src/example.py"
  start_line: 10
  end_line: 12
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            case_path = temp_path / "synthetic_run.yaml"
            repository_dir = temp_path / "repository"
            why_blame_main = temp_path / "main.py"

            case_path.write_text(
                text,
                encoding="utf-8",
            )

            case = parse_execution_case(
                case_path
            )

            run_case(
                case,
                repository_dir,
                why_blame_main,
            )

        mock_run.assert_called_once()

        call = mock_run.call_args

        self.assertEqual(
            call.args[0],
            [
                sys.executable,
                str(why_blame_main),
                "src/example.py",
                "10",
                "12",
            ],
        )
        self.assertEqual(
            call.kwargs["cwd"],
            str(repository_dir),
        )
        self.assertTrue(
            call.kwargs["capture_output"]
        )
        self.assertTrue(
            call.kwargs["text"]
        )
        self.assertEqual(
            call.kwargs["encoding"],
            "utf-8",
        )
        self.assertEqual(
            call.kwargs["errors"],
            "replace",
        )
        self.assertEqual(
            call.kwargs["env"]["PYTHONIOENCODING"],
            "utf-8",
        )


    def test_write_case_output_preserves_stdout_and_stderr(self):
        class Result:
            returncode = 1
            stdout = "WHY-BLAME\npartial output\n"
            stderr = "runtime failure\n"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            path = write_case_output(
                "synthetic_001",
                Result(),
                output_dir,
            )

            rendered = path.read_text(
                encoding="utf-8",
            )

        self.assertEqual(
            path.name,
            "synthetic_001.txt",
        )
        self.assertIn(
            "WHY-BLAME",
            rendered,
        )
        self.assertIn(
            "partial output",
            rendered,
        )
        self.assertIn(
            "runtime failure",
            rendered,
        )


    @patch("benchmark.holdout.run_holdout.write_case_output")
    @patch("benchmark.holdout.run_holdout.run_case")
    @patch("benchmark.holdout.run_holdout.prepare_repository")
    def test_run_candidate_case_connects_prepare_run_and_write(
        self,
        mock_prepare,
        mock_run_case,
        mock_write,
    ):
        text = """
id: synthetic_orchestration

repository:
  url: "https://example.invalid/project"

revision:
  commit: "abc123"

target:
  file: "src/example.py"
  start_line: 10
  end_line: 12
"""

        class Result:
            returncode = 0
            stdout = "WHY-BLAME\n"
            stderr = ""

        mock_run_case.return_value = Result()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            case_path = temp_path / "case.yaml"
            repository_dir = temp_path / "repository"
            output_dir = temp_path / "candidate_run"
            why_blame_main = temp_path / "main.py"

            case_path.write_text(
                text,
                encoding="utf-8",
            )

            case = parse_execution_case(
                case_path
            )

            run_candidate_case(
                case,
                repository_dir,
                why_blame_main,
                output_dir,
            )

        mock_prepare.assert_called_once_with(
            case.repository_url,
            case.commit,
            repository_dir,
        )

        mock_run_case.assert_called_once_with(
            case,
            repository_dir,
            why_blame_main,
        )

        mock_write.assert_called_once_with(
            case.case_id,
            mock_run_case.return_value,
            output_dir,
        )


    @patch("benchmark.holdout.run_holdout.run_candidate_case")
    @patch("benchmark.holdout.run_holdout.resolve_execution_case")
    @patch("benchmark.holdout.run_holdout.discover_case_paths")
    def test_main_runs_discovered_cases(
        self,
        mock_discover,
        mock_resolve,
        mock_run_candidate,
    ):
        case_path = Path("cases") / "synthetic_001.yaml"

        class Case:
            case_id = "synthetic_001"

        case = Case()

        mock_discover.return_value = [case_path]
        mock_resolve.return_value = case

        main([
            "--cases-dir",
            "cases",
            "--output-dir",
            "current_run",
            "--work-dir",
            "candidate_repos",
            "--why-blame-main",
            "main.py",
        ])

        mock_discover.assert_called_once_with(
            Path("cases"),
        )
        holdout_dir = Path(__file__).resolve().parent / "benchmark" / "holdout"

        mock_resolve.assert_called_once_with(
            case_path,
            holdout_dir / "results" / "synthetic_001.txt",
            holdout_dir / "current_run" / "synthetic_001.txt",
        )
        mock_run_candidate.assert_called_once_with(
            case,
            Path("candidate_repos") / "synthetic_001",
            Path("main.py"),
            Path("current_run"),
        )
if __name__ == "__main__":
    unittest.main()
