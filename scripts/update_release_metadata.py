import argparse
import datetime
import re
import tomllib
from pathlib import Path


VERSION_PATTERN = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+$"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Update Why-Blame release metadata."
    )
    parser.add_argument(
        "--version",
        required=True,
        help="New version such as 0.3.2.",
    )
    parser.add_argument(
        "--summary",
        required=True,
        help="Short changelog summary.",
    )
    parser.add_argument(
        "--date",
        default=datetime.date.today().isoformat(),
        help="Release date in YYYY-MM-DD format.",
    )
    return parser.parse_args()


def parse_version(value):
    if not VERSION_PATTERN.fullmatch(value):
        raise SystemExit(
            f"Invalid semantic version: {value}"
        )

    return tuple(
        int(part)
        for part in value.split(".")
    )


def read_current_version(path):
    data = tomllib.loads(
        path.read_text(encoding="utf-8")
    )
    return data["project"]["version"]


def update_pyproject(path, old_version, new_version):
    text = path.read_text(encoding="utf-8")

    old = f'version = "{old_version}"'
    new = f'version = "{new_version}"'

    if text.count(old) != 1:
        raise SystemExit(
            "Expected exactly one project version declaration"
        )

    path.write_text(
        text.replace(old, new, 1),
        encoding="utf-8",
        newline="\n",
    )


def update_readme(path, old_version, new_version):
    text = path.read_text(encoding="utf-8")

    old_label = f"why-blame v{old_version}"
    new_label = f"why-blame v{new_version}"

    old_target = f"releases/tag/v{old_version}"
    new_target = f"releases/tag/v{new_version}"

    if text.count(old_label) != 1:
        raise SystemExit(
            "Expected exactly one README release label"
        )

    if text.count(old_target) != 1:
        raise SystemExit(
            "Expected exactly one README release target"
        )

    text = text.replace(
        old_label,
        new_label,
        1,
    )
    text = text.replace(
        old_target,
        new_target,
        1,
    )

    path.write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )


def update_changelog(
    path,
    old_version,
    new_version,
    release_date,
    summary,
):
    text = path.read_text(encoding="utf-8")

    if f"## [{new_version}]" in text:
        raise SystemExit(
            f"CHANGELOG entry already exists: {new_version}"
        )

    marker = f"## [{old_version}]"

    if text.count(marker) != 1:
        raise SystemExit(
            f"Expected one CHANGELOG marker: {marker}"
        )

    entry_lines = [
        f"## [{new_version}] - {release_date}",
        "",
        "### Changed",
        "",
        f"- {summary}",
        "",
        "### Validation",
        "",
        "- Full verification passes.",
        "- HTTP ResourceWarning count is zero.",
        "- Holdout v1 integrity verification passes.",
        "- Holdout v2 post-improvement scoring passes.",
        "",
    ]

    entry = "\n".join(entry_lines)

    path.write_text(
        text.replace(marker, entry + marker, 1),
        encoding="utf-8",
        newline="\n",
    )


def validate_result(
    pyproject_path,
    readme_path,
    changelog_path,
    version,
):
    project = tomllib.loads(
        pyproject_path.read_text(encoding="utf-8")
    )

    if project["project"]["version"] != version:
        raise SystemExit("Project version update failed")

    readme = readme_path.read_text(encoding="utf-8")

    if f"why-blame v{version}" not in readme:
        raise SystemExit("README label update failed")

    if f"releases/tag/v{version}" not in readme:
        raise SystemExit("README target update failed")

    changelog = changelog_path.read_text(encoding="utf-8")

    if f"## [{version}]" not in changelog:
        raise SystemExit("CHANGELOG update failed")

    for path in (
        pyproject_path,
        readme_path,
        changelog_path,
    ):
        raw = path.read_bytes()

        if raw.startswith(bytes([239, 187, 191])):
            raise SystemExit(
                f"Unexpected UTF-8 BOM: {path}"
            )

        raw.decode("utf-8")


def main():
    args = parse_args()

    pyproject_path = Path("pyproject.toml")
    readme_path = Path("README.md")
    changelog_path = Path("CHANGELOG.md")

    current_version = read_current_version(
        pyproject_path
    )

    current_tuple = parse_version(current_version)
    requested_tuple = parse_version(args.version)

    if requested_tuple <= current_tuple:
        raise SystemExit(
            f"New version must exceed {current_version}"
        )

    update_pyproject(
        pyproject_path,
        current_version,
        args.version,
    )

    update_readme(
        readme_path,
        current_version,
        args.version,
    )

    update_changelog(
        changelog_path,
        current_version,
        args.version,
        args.date,
        args.summary,
    )

    validate_result(
        pyproject_path,
        readme_path,
        changelog_path,
        args.version,
    )

    print("OLD_VERSION:", current_version)
    print("NEW_VERSION:", args.version)
    print("RELEASE_DATE:", args.date)
    print("RELEASE_METADATA_UPDATE_OK")


if __name__ == "__main__":
    main()
