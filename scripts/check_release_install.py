import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Install and validate a Why-Blame wheel."
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Expected installed version.",
    )
    parser.add_argument(
        "--dist-dir",
        default="dist",
        help="Directory containing the wheel.",
    )
    return parser.parse_args()


def run(command, cwd=None):
    print("RUN:", " ".join(str(part) for part in command))

    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
    )

    if result.returncode != 0:
        raise SystemExit(
            f"Command failed with exit code "
            f"{result.returncode}: {command}"
        )



def run_capture(command, cwd=None):
    print("RUN:", " ".join(str(part) for part in command))

    result = subprocess.run(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if result.returncode != 0:
        raise ValueError(
            f"Command failed with exit code {result.returncode}: "
            f"{command!r}; stderr={result.stderr!r}"
        )

    return result


def validate_json_output(
    stdout_bytes,
    stderr_bytes,
    expected_file,
    expected_line,
):
    if stderr_bytes:
        raise ValueError(
            f"Expected empty stderr, got: {stderr_bytes!r}"
        )

    if not stdout_bytes:
        raise ValueError("JSON stdout is empty.")

    try:
        stdout_text = stdout_bytes.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError(
            "JSON stdout is not ASCII-safe."
        ) from exc

    try:
        document = json.loads(stdout_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "CLI did not produce one valid JSON document."
        ) from exc

    if document.get("schema_version") != "1":
        raise ValueError("Unexpected JSON schema version.")

    expected_target = {
        "file": expected_file,
        "start_line": expected_line,
        "end_line": expected_line,
    }

    if document.get("target") != expected_target:
        raise ValueError(
            f"Unexpected JSON target: {document.get('target')!r}"
        )

    repository = document.get("repository")

    if repository is not None and not isinstance(
        repository,
        dict,
    ):
        raise ValueError(
            "JSON repository must be an object or null."
        )

    if not isinstance(document.get("current_lines"), list):
        raise ValueError(
            "JSON current_lines must be an array."
        )

    timeline = document.get("timeline")

    if not isinstance(timeline, list) or not timeline:
        raise ValueError(
            "JSON timeline must be a non-empty array."
        )

    if not isinstance(document.get("stats"), dict):
        raise ValueError(
            "JSON stats must be an object."
        )

    return document



def validate_json_error_output(
    stdout_bytes,
    stderr_bytes,
    return_code,
    expected_exit_code,
    expected_error_code,
):
    if return_code != expected_exit_code:
        raise ValueError(
            f"Unexpected JSON error exit code: {return_code}"
        )

    if stderr_bytes:
        raise ValueError(
            "Expected empty stderr from JSON error mode, got: "
            + repr(stderr_bytes)
        )

    if not stdout_bytes:
        raise ValueError(
            "JSON error mode produced empty stdout."
        )

    try:
        stdout_text = stdout_bytes.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError(
            "JSON error output is not ASCII-safe."
        ) from exc

    try:
        document = json.loads(stdout_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "JSON error mode did not produce one valid document."
        ) from exc

    if document.get("schema_version") != "1":
        raise ValueError(
            "Unexpected JSON error schema version."
        )

    error = document.get("error")

    if not isinstance(error, dict):
        raise ValueError(
            "JSON error document must contain an error object."
        )

    if error.get("code") != expected_error_code:
        raise ValueError(
            f"Unexpected JSON error code: {error.get('code')!r}"
        )

    if not isinstance(error.get("message"), str):
        raise ValueError(
            "JSON error message must be a string."
        )

    if not error["message"]:
        raise ValueError(
            "JSON error message must not be empty."
        )

    return document

def initialize_sample_repository(sample_repo):
    sample_repo.mkdir(
        parents=True,
        exist_ok=True,
    )

    service_path = sample_repo / "service.py"
    service_path.write_text(
        "def pay(user):\n"
        "    return user.is_active\n",
        encoding="utf-8",
    )

    run(
        ["git", "init"],
        cwd=sample_repo,
    )
    run(
        [
            "git",
            "config",
            "user.email",
            "release-check@example.invalid",
        ],
        cwd=sample_repo,
    )
    run(
        [
            "git",
            "config",
            "user.name",
            "Why-Blame Release Check",
        ],
        cwd=sample_repo,
    )
    run(
        [
            "git",
            "add",
            "service.py",
        ],
        cwd=sample_repo,
    )
    run(
        [
            "git",
            "commit",
            "-m",
            "Add sample service",
        ],
        cwd=sample_repo,
    )

def main():
    args = parse_args()
    dist_dir = Path(args.dist_dir).resolve()

    wheels = list(
        dist_dir.glob(
            f"why_blame-{args.version}-*.whl"
        )
    )

    if len(wheels) != 1:
        raise SystemExit(
            f"Expected exactly one wheel, got: {wheels}"
        )

    wheel = wheels[0]
    temp_root = Path(
        tempfile.mkdtemp(
            prefix="why-blame-release-"
        )
    )

    try:
        venv_dir = temp_root / "venv"

        run(
            [
                sys.executable,
                "-m",
                "venv",
                str(venv_dir),
            ]
        )

        if os.name == "nt":
            python_exe = (
                venv_dir
                / "Scripts"
                / "python.exe"
            )
            cli_exe = (
                venv_dir
                / "Scripts"
                / "why-blame.exe"
            )
        else:
            python_exe = (
                venv_dir
                / "bin"
                / "python"
            )
            cli_exe = (
                venv_dir
                / "bin"
                / "why-blame"
            )

        run(
            [
                str(python_exe),
                "-m",
                "pip",
                "install",
                str(wheel),
            ]
        )

        version_code = (
            "from importlib.metadata import version; "
            "value = version('why-blame'); "
            "print('INSTALLED_VERSION:', value); "
            f"assert value == '{args.version}'"
        )

        run(
            [
                str(python_exe),
                "-c",
                version_code,
            ]
        )

        if not cli_exe.is_file():
            raise SystemExit(
                f"Installed CLI not found: {cli_exe}"
            )

        run(
            [
                str(cli_exe),
                "--help",
            ],
            cwd=temp_root,
        )

        sample_repo = temp_root / "sample-repository"

        initialize_sample_repository(
            sample_repo
        )

        json_result = run_capture(
            [
                str(cli_exe),
                "service.py:2",
                "--json",
            ],
            cwd=sample_repo,
        )

        document = validate_json_output(
            json_result.stdout,
            json_result.stderr,
            expected_file="service.py",
            expected_line=2,
        )

        print(
            "JSON_SCHEMA_VERSION:",
            document["schema_version"],
        )
        print(
            "JSON_TIMELINE_EVENTS:",
            len(document["timeline"]),
        )
        print(
            "JSON_CONFIDENCE:",
            document["stats"].get(
                "confidence",
                "UNKNOWN",
            ),
        )
        print("RELEASE_JSON_CHECK_OK")

        json_error_result = subprocess.run(
            [str(cli_exe), "--json"],
            cwd=sample_repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        error_document = validate_json_error_output(
            json_error_result.stdout,
            json_error_result.stderr,
            json_error_result.returncode,
            expected_exit_code=2,
            expected_error_code="INVALID_ARGUMENTS",
        )

        print(
            "JSON_ERROR_EXIT_CODE:",
            json_error_result.returncode,
        )
        print(
            "JSON_ERROR_CODE:",
            error_document["error"]["code"],
        )
        print("RELEASE_JSON_ERROR_CHECK_OK")
        missing_result = subprocess.run(
            [str(cli_exe), "missing.py:1", "--json"],
            cwd=sample_repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        validate_json_error_output(
            missing_result.stdout,
            missing_result.stderr,
            missing_result.returncode,
            1,
            "FILE_NOT_FOUND",
        )

        print("FILE_NOT_FOUND_CHECK_OK")

        non_git_repo = temp_root / "non-git-repository"
        non_git_repo.mkdir()

        (non_git_repo / "service.py").write_text(
            "def example():\n"
            "    return True\n",
            encoding="utf-8",
        )

        non_git_result = subprocess.run(
            [str(cli_exe), "service.py:2", "--json"],
            cwd=non_git_repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        validate_json_error_output(
            non_git_result.stdout,
            non_git_result.stderr,
            non_git_result.returncode,
            1,
            "NOT_A_GIT_REPOSITORY",
        )

        print("NOT_A_GIT_REPOSITORY_CHECK_OK")
        print("RELEASE_RUNTIME_ERROR_CHECK_OK")
        print("RELEASE_INSTALL_CHECK_OK")
    finally:
        shutil.rmtree(
            temp_root,
            ignore_errors=True,
        )


if __name__ == "__main__":
    main()
