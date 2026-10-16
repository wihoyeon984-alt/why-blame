import argparse
import hashlib
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Create and verify SHA-256 checksums "
            "for Why-Blame release artifacts."
        )
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Release version such as 0.3.2.",
    )
    parser.add_argument(
        "--dist-dir",
        default="dist",
        help="Directory containing release artifacts.",
    )
    return parser.parse_args()


def sha256(path):
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def require_one(paths, description):
    paths = list(paths)

    if len(paths) != 1:
        raise SystemExit(
            f"Expected exactly one {description}, got: {paths}"
        )

    return paths[0]


def main():
    args = parse_args()
    dist_dir = Path(args.dist_dir)

    if not dist_dir.is_dir():
        raise SystemExit(
            f"Distribution directory not found: {dist_dir}"
        )

    wheel = require_one(
        dist_dir.glob(
            f"why_blame-{args.version}-*.whl"
        ),
        "wheel",
)

    sdist = require_one(
        dist_dir.glob(
            f"why_blame-{args.version}.tar.gz"
        ),
        "source distribution",
    )

    artifacts = (
        wheel,
        sdist,
    )

    checksum_path = dist_dir / "SHA256SUMS.txt"

    lines = [
        f"{sha256(path)}  {path.name}"
        for path in artifacts
    ]

    checksum_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    stored_lines = checksum_path.read_text(
        encoding="utf-8"
    ).splitlines()

    if len(stored_lines) != len(artifacts):
        raise SystemExit(
            "Unexpected checksum entry count"
        )

    for line in stored_lines:
        parts = line.split("  ", 1)

        if len(parts) != 2:
            raise SystemExit(
                f"Invalid checksum line: {line}"
            )

        expected, filename = parts
        artifact = dist_dir / filename

        if not artifact.is_file():
            raise SystemExit(
                f"Missing release artifact: {filename}"
            )

        actual = sha256(artifact)

        if actual != expected:
            raise SystemExit(
                f"SHA-256 mismatch: {filename}"
            )

        print(filename, "SHA256_OK")

    raw = checksum_path.read_bytes()

    if raw.startswith(bytes([239, 187, 191])):
        raise SystemExit(
            "Unexpected UTF-8 BOM in SHA256SUMS.txt"
        )

    print("CHECKSUM_FILE:", checksum_path)
    print("RELEASE_CHECKSUMS_OK")


if __name__ == "__main__":
    main()
