import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

from benchmark.holdout_v2.run_current_main_snapshot import (
    CommandResult,
    ExecutionSpec,
    RepositoryCheckout,
    SnapshotError,
    build_file_manifest,
    checkout_product_worktree,
    clone_frozen_repository,
    decode_utf8_strict,
    ensure_new_output_directory,
    load_execution_specs,
    read_git_head,
    remove_product_worktree,
    require_success,
    run_command,
    run_single_case_snapshot,
    run_why_blame,
    select_execution_spec,
    sha256_file,
    write_case_artifacts,
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


    def test_decode_utf8_strict_accepts_valid_text(self):
        text = decode_utf8_strict(
            "?? ??".encode("utf-8"),
            "stdout",
        )

        self.assertEqual(
            text,
            "?? ??",
        )

    def test_decode_utf8_strict_rejects_invalid_bytes(self):
        with self.assertRaisesRegex(
            SnapshotError,
            "not valid UTF-8",
        ):
            decode_utf8_strict(
                b"\xff\xfe",
                "stdout",
            )

    def test_run_why_blame_preserves_exact_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repository = root / "repository"
            repository.mkdir()

            target = repository / "sample.py"
            target.write_text(
                "print('sample')\n",
                encoding="utf-8",
            )

            fake_main = root / "fake_main.py"
            fake_main.write_text(
                (
                    "import sys\n"
                    "sys.stdout.buffer.write("
                    "'?? ??'.encode('utf-8'))\n"
                    "sys.stderr.buffer.write(b'')\n"
                ),
                encoding="utf-8",
            )

            spec = ExecutionSpec(
                case_id="sample_001",
                repository_url=(
                    "https://example.invalid/repository.git"
                ),
                repository_commit="a" * 40,
                target_file="sample.py",
                start_line=1,
                end_line=1,
            )

            result = run_why_blame(
                spec,
                repository,
                sys.executable,
                fake_main,
            )

            self.assertEqual(
                result.exit_code,
                0,
            )
            self.assertEqual(
                result.stdout,
                "?? ??".encode("utf-8"),
            )
            self.assertEqual(
                result.stderr,
                b"",
            )

    def test_write_case_artifacts_preserves_bytes_and_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "result"

            spec = ExecutionSpec(
                case_id="sample_001",
                repository_url=(
                    "https://example.invalid/repository.git"
                ),
                repository_commit="a" * 40,
                target_file="sample.py",
                start_line=1,
                end_line=2,
            )

            checkout = RepositoryCheckout(
                repository_path=str(
                    root / "repository"
                ),
                requested_commit="a" * 40,
                checked_out_commit="a" * 40,
            )

            result = CommandResult(
                command=(
                    sys.executable,
                    "main.py",
                    spec.target,
                ),
                working_directory=str(
                    root / "repository"
                ),
                exit_code=0,
                stdout="?? ??\n".encode("utf-8"),
                stderr=b"",
                started_at_utc=(
                    "2026-10-18T10:00:00+00:00"
                ),
                finished_at_utc=(
                    "2026-10-18T10:00:01+00:00"
                ),
            )

            metadata = write_case_artifacts(
                output,
                spec,
                checkout,
                result,
                "b" * 40,
                "c" * 40,
            )

            self.assertEqual(
                (output / "stdout.bin").read_bytes(),
                result.stdout,
            )
            self.assertEqual(
                (output / "stderr.bin").read_bytes(),
                b"",
            )
            self.assertEqual(
                (output / "stdout.txt").read_text(
                    encoding="utf-8"
                ),
                "?? ??\n",
            )
            self.assertEqual(
                metadata[
                    "evaluated_product_commit"
                ],
                "b" * 40,
            )
            self.assertEqual(
                metadata[
                    "snapshot_runner_commit"
                ],
                "c" * 40,
            )
            self.assertEqual(
                metadata["artifacts"]["stdout_sha256"],
                hashlib.sha256(
                    result.stdout
                ).hexdigest().upper(),
            )

            stored_metadata = json.loads(
                (output / "metadata.json").read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(
                stored_metadata,
                metadata,
            )


    def test_checkout_product_worktree_uses_requested_commit(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source, unused_commit = (
                self._create_local_git_repository(temp_dir)
            )

            (source / "main.py").write_text(
                "print('product')\n",
                encoding="utf-8",
            )

            require_success(
                run_command(
                    ["git", "add", "main.py"],
                    source,
                ),
                "stage product main",
            )

            require_success(
                run_command(
                    ["git", "commit", "-m", "add product main"],
                    source,
                ),
                "commit product main",
            )

            product_commit = read_git_head(source)
            destination = Path(temp_dir) / "product-worktree"

            checkout = checkout_product_worktree(
                source,
                destination,
                product_commit,
            )

            self.assertEqual(
                checkout.requested_commit,
                product_commit,
            )
            self.assertEqual(
                checkout.checked_out_commit,
                product_commit,
            )
            self.assertTrue(
                (destination / "main.py").is_file()
            )

            remove_product_worktree(
                source,
                destination,
            )

            self.assertFalse(destination.exists())

    def test_checkout_product_worktree_rejects_existing_destination(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source, commit = (
                self._create_local_git_repository(temp_dir)
            )
            destination = Path(temp_dir) / "product-worktree"
            destination.mkdir()

            with self.assertRaisesRegex(
                SnapshotError,
                "already exists",
            ):
                checkout_product_worktree(
                    source,
                    destination,
                    commit,
                )


    def test_select_execution_spec_returns_requested_case(self):
        specs = [
            ExecutionSpec(
                case_id="sample_001",
                repository_url="repository-one",
                repository_commit="a" * 40,
                target_file="sample.py",
                start_line=1,
                end_line=1,
            ),
            ExecutionSpec(
                case_id="sample_002",
                repository_url="repository-two",
                repository_commit="b" * 40,
                target_file="other.py",
                start_line=2,
                end_line=3,
            ),
        ]

        selected = select_execution_spec(
            specs,
            "sample_002",
        )

        self.assertEqual(
            selected.case_id,
            "sample_002",
        )

    def test_select_execution_spec_rejects_unknown_case(self):
        with self.assertRaisesRegex(
            SnapshotError,
            "found 0",
        ):
            select_execution_spec(
                [],
                "missing_001",
            )

    def test_run_single_case_snapshot_preserves_artifacts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            product_root = root / "product-repository-root"
            product_root.mkdir()

            product_repository, unused_commit = (
                self._create_local_git_repository(
                    product_root
                )
            )

            product_main = (
                product_repository
                / "main.py"
            )

            product_main.write_text(
                (
                    "import sys\n"
                    "target = sys.argv[1]\n"
                    "print('WHY-BLAME')\n"
                    "print('TARGET: ' + target)\n"
                    "print('?? ??')\n"
                ),
                encoding="utf-8",
            )

            require_success(
                run_command(
                    ["git", "add", "main.py"],
                    product_repository,
                ),
                "stage product main",
            )

            require_success(
                run_command(
                    [
                        "git",
                        "commit",
                        "-m",
                        "add product main",
                    ],
                    product_repository,
                ),
                "commit product main",
            )

            evaluated_commit = read_git_head(
                product_repository
            )

            external_root = root / "external-repository-root"
            external_root.mkdir()

            external_repository, external_commit = (
                self._create_local_git_repository(
                    external_root
                )
            )

            sample_target = (
                external_repository
                / "sample.py"
            )

            sample_target.write_text(
                "print('sample')\n",
                encoding="utf-8",
            )

            require_success(
                run_command(
                    ["git", "add", "sample.py"],
                    external_repository,
                ),
                "stage external target",
            )

            require_success(
                run_command(
                    [
                        "git",
                        "commit",
                        "-m",
                        "add external target",
                    ],
                    external_repository,
                ),
                "commit external target",
            )

            external_commit = read_git_head(
                external_repository
            )

            holdout_dir = root / "holdout"
            cases_dir = holdout_dir / "cases"
            candidates_dir = holdout_dir / "candidates"

            cases_dir.mkdir(parents=True)
            candidates_dir.mkdir(parents=True)

            case = {
                "schema_version": 2,
                "case_id": "sample_001",
                "repository": {
                    "url": str(external_repository),
                    "commit": external_commit,
                },
                "frozen": True,
                "claims": {},
            }

            candidate = {
                "schema_version": 2,
                "candidate_id": "sample_001",
                "repository": {
                    "url": str(external_repository),
                    "commit": external_commit,
                },
                "target": {
                    "file": "sample.py",
                    "start_line": 1,
                    "end_line": 1,
                },
            }

            (cases_dir / "sample_001.json").write_text(
                json.dumps(case),
                encoding="utf-8",
            )

            (
                candidates_dir
                / "sample_001.json"
            ).write_text(
                json.dumps(candidate),
                encoding="utf-8",
            )

            workspace = root / "workspace"
            runner_commit = "c" * 40

            captured = run_single_case_snapshot(
                product_repository,
                holdout_dir,
                workspace,
                "sample_001",
                evaluated_commit,
                runner_commit,
                sys.executable,
            )

            result_directory = Path(
                captured["result_directory"]
            )

            self.assertTrue(
                (result_directory / "stdout.bin").is_file()
            )
            self.assertTrue(
                (result_directory / "stderr.bin").is_file()
            )
            self.assertTrue(
                (result_directory / "stdout.txt").is_file()
            )
            self.assertTrue(
                (result_directory / "stderr.txt").is_file()
            )
            self.assertTrue(
                (result_directory / "metadata.json").is_file()
            )

            stdout_text = (
                result_directory
                / "stdout.txt"
            ).read_text(
                encoding="utf-8"
            )

            self.assertIn(
                "WHY-BLAME",
                stdout_text,
            )
            self.assertIn(
                "sample.py:1-1",
                stdout_text,
            )
            self.assertIn(
                "?? ??",
                stdout_text,
            )

            metadata = captured["metadata"]

            self.assertEqual(
                metadata[
                    "evaluated_product_commit"
                ],
                evaluated_commit,
            )
            self.assertEqual(
                metadata[
                    "snapshot_runner_commit"
                ],
                runner_commit,
            )
            self.assertEqual(
                metadata["execution"]["exit_code"],
                0,
            )
            self.assertEqual(
                metadata["artifacts"]["stderr_bytes"],
                0,
            )

            self.assertFalse(
                (workspace / "product").exists()
            )


if __name__ == "__main__":
    unittest.main()
