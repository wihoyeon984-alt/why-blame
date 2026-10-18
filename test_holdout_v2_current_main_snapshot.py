import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

from benchmark.holdout_v2.run_current_main_snapshot import (
    ExecutionSpec,
    SnapshotError,
    build_file_manifest,
    clone_frozen_repository,
    ensure_new_output_directory,
    load_execution_specs,
    read_git_head,
    require_success,
    run_command,
    sha256_file,
)


class TestCurrentMainSnapshotRunner(unittest.TestCase):

    def test_sha256_file_hashes_exact_bytes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "artifact.bin"
            path.write_bytes(b"why-blame\n")

            expected = hashlib.sha256(
                b"why-blame\n"
            ).hexdigest().upper()

            self.assertEqual(
                sha256_file(path),
                expected,
            )

    def test_build_file_manifest_uses_relative_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            nested = root / "case" / "stdout.txt"
            nested.parent.mkdir()
            nested.write_bytes(b"output")

            manifest = build_file_manifest(root)

            self.assertEqual(len(manifest), 1)
            self.assertEqual(
                manifest[0]["relative_path"],
                "case/stdout.txt",
            )
            self.assertEqual(
                manifest[0]["length"],
                6,
            )
            self.assertEqual(
                manifest[0]["sha256"],
                hashlib.sha256(
                    b"output"
                ).hexdigest().upper(),
            )

    def test_build_file_manifest_is_sorted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "z.txt").write_text(
                "z",
                encoding="utf-8",
            )
            (root / "a.txt").write_text(
                "a",
                encoding="utf-8",
            )

            manifest = build_file_manifest(root)

            self.assertEqual(
                [
                    item["relative_path"]
                    for item in manifest
                ],
                [
                    "a.txt",
                    "z.txt",
                ],
            )

    def test_ensure_new_output_directory_rejects_existing_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            existing = Path(temp_dir) / "snapshot"
            existing.mkdir()

            with self.assertRaisesRegex(
                SnapshotError,
                "already exists",
            ):
                ensure_new_output_directory(existing)

    def test_ensure_new_output_directory_creates_new_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "snapshot"

            ensure_new_output_directory(output)

            self.assertTrue(output.is_dir())

    def test_load_execution_specs_reads_frozen_cases(self):
        repository_root = Path(__file__).parent
        holdout_dir = (
            repository_root
            / "benchmark"
            / "holdout_v2"
        )

        specs = load_execution_specs(holdout_dir)

        self.assertEqual(len(specs), 10)
        self.assertEqual(
            specs[0].case_id,
            "aiohttp_001",
        )
        self.assertEqual(
            specs[-1].case_id,
            "urllib3_001",
        )

    def test_load_execution_specs_preserves_requests_target(self):
        repository_root = Path(__file__).parent
        holdout_dir = (
            repository_root
            / "benchmark"
            / "holdout_v2"
        )

        specs = {
            spec.case_id: spec
            for spec in load_execution_specs(
                holdout_dir
            )
        }

        requests = specs["requests_003"]

        self.assertEqual(
            requests.repository_commit,
            "6f205ff422bccd5e4c4fc0b64c5f3e7df5181db6",
        )
        self.assertEqual(
            requests.target,
            "src/requests/models.py:237-246",
        )

    def test_load_execution_specs_rejects_missing_candidate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            holdout_dir = Path(temp_dir)
            cases_dir = holdout_dir / "cases"
            candidates_dir = holdout_dir / "candidates"

            cases_dir.mkdir()
            candidates_dir.mkdir()

            case = {
                "schema_version": 2,
                "case_id": "sample_001",
                "repository": {
                    "url": "https://example.invalid/repository.git",
                    "commit": "a" * 40,
                },
                "frozen": True,
                "claims": {},
            }

            (cases_dir / "sample_001.json").write_text(
                json.dumps(case),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                SnapshotError,
                "candidate",
            ):
                load_execution_specs(holdout_dir)


    def test_run_command_preserves_exact_bytes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            script = (
                "import sys; "
                "sys.stdout.buffer.write(b'out\\x00put'); "
                "sys.stderr.buffer.write(b'error')"
            )

            result = run_command(
                [sys.executable, "-c", script],
                temp_dir,
            )

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.stdout, b"out\x00put")
            self.assertEqual(result.stderr, b"error")
            self.assertEqual(result.command[0], sys.executable)
            self.assertEqual(
                Path(result.working_directory),
                Path(temp_dir).resolve(),
            )

    def test_run_command_rejects_empty_command(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(
                SnapshotError,
                "must not be empty",
            ):
                run_command([], temp_dir)

    def test_run_command_rejects_missing_working_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing"

            with self.assertRaisesRegex(
                SnapshotError,
                "working directory",
            ):
                run_command(
                    [sys.executable, "-c", "pass"],
                    missing,
                )

    def test_require_success_returns_successful_result(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_command(
                [sys.executable, "-c", "print('ok')"],
                temp_dir,
            )

            self.assertIs(
                require_success(result, "test"),
                result,
            )

    def test_require_success_rejects_failed_command(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            script = (
                "import sys; "
                "sys.stderr.write('failed'); "
                "raise SystemExit(7)"
            )

            result = run_command(
                [sys.executable, "-c", script],
                temp_dir,
            )

            with self.assertRaisesRegex(
                SnapshotError,
                "exit code 7",
            ):
                require_success(
                    result,
                    "test operation",
                )


    def _create_local_git_repository(self, root):
        source = Path(root) / "source"
        source.mkdir()

        require_success(
            run_command(
                ["git", "init"],
                source,
            ),
            "initialize test repository",
        )

        require_success(
            run_command(
                [
                    "git",
                    "config",
                    "user.name",
                    "Snapshot Test",
                ],
                source,
            ),
            "configure test user name",
        )

        require_success(
            run_command(
                [
                    "git",
                    "config",
                    "user.email",
                    "snapshot@example.invalid",
                ],
                source,
            ),
            "configure test user email",
        )

        tracked = source / "tracked.txt"
        tracked.write_text(
            "frozen content\n",
            encoding="utf-8",
        )

        require_success(
            run_command(
                ["git", "add", "tracked.txt"],
                source,
            ),
            "stage test file",
        )

        require_success(
            run_command(
                ["git", "commit", "-m", "frozen commit"],
                source,
            ),
            "create test commit",
        )

        commit = read_git_head(source)

        return source, commit

    def test_read_git_head_returns_full_commit(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source, commit = (
                self._create_local_git_repository(
                    temp_dir
                )
            )

            self.assertEqual(
                read_git_head(source),
                commit,
            )
            self.assertEqual(len(commit), 40)

    def test_clone_frozen_repository_checks_out_requested_commit(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source, commit = (
                self._create_local_git_repository(
                    temp_dir
                )
            )

            spec = ExecutionSpec(
                case_id="sample_001",
                repository_url=str(source),
                repository_commit=commit,
                target_file="tracked.txt",
                start_line=1,
                end_line=1,
            )

            destination = (
                Path(temp_dir)
                / "checkout"
            )

            checkout = clone_frozen_repository(
                spec,
                destination,
            )

            self.assertEqual(
                checkout.requested_commit,
                commit,
            )
            self.assertEqual(
                checkout.checked_out_commit,
                commit,
            )
            self.assertEqual(
                Path(checkout.repository_path),
                destination.resolve(),
            )
            self.assertEqual(
                (destination / "tracked.txt").read_text(
                    encoding="utf-8"
                ),
                "frozen content\n",
            )

    def test_clone_frozen_repository_rejects_existing_destination(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source, commit = (
                self._create_local_git_repository(
                    temp_dir
                )
            )

            destination = Path(temp_dir) / "checkout"
            destination.mkdir()

            spec = ExecutionSpec(
                case_id="sample_001",
                repository_url=str(source),
                repository_commit=commit,
                target_file="tracked.txt",
                start_line=1,
                end_line=1,
            )

            with self.assertRaisesRegex(
                SnapshotError,
                "already exists",
            ):
                clone_frozen_repository(
                    spec,
                    destination,
                )


if __name__ == "__main__":
    unittest.main()
