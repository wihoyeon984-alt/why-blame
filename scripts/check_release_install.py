import argparse
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

        print("RELEASE_INSTALL_CHECK_OK")
    finally:
        shutil.rmtree(
            temp_root,
            ignore_errors=True,
        )


if __name__ == "__main__":
    main()