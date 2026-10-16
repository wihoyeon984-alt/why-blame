import argparse
import tarfile
import zipfile
from pathlib import Path


REQUIRED_MODULES = (
    "main.py",
    "github_client.py",
    "claim_adapter.py",
    "claim_policy.py",
    "claim_safe_renderer.py",
    "claim_semantic_extractor.py",
    "claim_semantics.py",
)

REQUIRED_SDIST_FILES = (
    "pyproject.toml",
    "README.md",
    "CHANGELOG.md",
    "main.py",
    "github_client.py",
    "claim_semantic_extractor.py",
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate Why-Blame release artifacts."
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Expected release version such as 0.3.2.",
    )
    parser.add_argument(
        "--dist-dir",
        default="dist",
        help="Directory containing the release artifacts.",
    )
    return parser.parse_args()


def require_one(paths, description):
    paths = list(paths)

    if len(paths) != 1:
        raise SystemExit(
            f"Expected exactly one {description}, got: {paths}"
        )

    return paths[0]


def check_wheel(dist_dir, version):
    wheel = require_one(
        dist_dir.glob(f"why_blame-{version}-*.whl"),
        "wheel",
    )

    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()

        metadata_files = [
            name
            for name in names
            if name.endswith(".dist-info/METADATA")
        ]

        metadata_name = require_one(
            metadata_files,
            "wheel metadata file",
        )

        metadata = archive.read(
            metadata_name
        ).decode("utf-8")

        required_metadata = (
            "Name: why-blame",
            f"Version: {version}",
            "Requires-Python: >=3.9",
        )

        for value in required_metadata:
            if value not in metadata:
                raise SystemExit(
                    f"Missing wheel metadata: {value}"
                )

        missing_modules = [
            module
            for module in REQUIRED_MODULES
            if module not in names
        ]

        if missing_modules:
            raise SystemExit(
                f"Missing wheel modules: {missing_modules}"
            )

    print(f"WHEEL: {wheel}")
    print("WHEEL_METADATA_OK")
    return wheel


def check_sdist(dist_dir, version):
    sdist = require_one(
        dist_dir.glob(f"why_blame-{version}.tar.gz"),
        "source distribution",
    )

    with tarfile.open(sdist, "r:gz") as archive:
        names = archive.getnames()

        missing_files = [
            filename
            for filename in REQUIRED_SDIST_FILES
            if not any(
                name.endswith("/" + filename)
                for name in names
            )
        ]

        if missing_files:
            raise SystemExit(
                f"Missing sdist files: {missing_files}"
            )

    print(f"SDIST: {sdist}")
    print("SDIST_CONTENTS_OK")
    return sdist


def main():
    args = parse_args()
    dist_dir = Path(args.dist_dir)

    if not dist_dir.is_dir():
        raise SystemExit(
            f"Distribution directory not found: {dist_dir}"
        )

    check_wheel(dist_dir, args.version)
    check_sdist(dist_dir, args.version)

    print("RELEASE_PACKAGE_CHECK_OK")


if __name__ == "__main__":
    main()