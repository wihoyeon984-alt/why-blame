from hashlib import sha256
from pathlib import Path
import sys


def main():
    manifest = Path(
        "benchmark/holdout/HOLDOUT_V1_SHA256.txt"
    )

    if not manifest.exists():
        print(
            "Holdout v1 manifest was not found.",
            file=sys.stderr,
        )
        return 1

    failures = []

    for raw_line in manifest.read_text(
        encoding="utf-8"
    ).splitlines():
        if not raw_line.strip():
            continue

        expected, relative = raw_line.split(
            "  ",
            1,
        )

        path = Path(relative)

        if not path.exists():
            failures.append(
                f"MISSING {relative}"
            )
            continue

        actual = sha256(
            path.read_bytes()
        ).hexdigest()

        if actual != expected:
            failures.append(
                f"CHANGED {relative}"
            )

    if failures:
        print(
            "Holdout v1 integrity check failed:"
        )

        for failure in failures:
            print(
                f"- {failure}"
            )

        return 1

    print(
        "Holdout v1 integrity check passed."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
