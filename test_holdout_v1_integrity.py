import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TestHoldoutV1Integrity(unittest.TestCase):

    def test_verifier_succeeds_outside_repository_root(self):
        verifier = (
            Path(__file__).resolve().parent
            / "benchmark"
            / "holdout"
            / "verify_v1_integrity.py"
        )

        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    sys.executable,
                    str(verifier),
                ],
                cwd=directory,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        self.assertEqual(
            result.returncode,
            0,
            msg=result.stdout + result.stderr,
        )
        self.assertIn(
            "Holdout v1 integrity check passed.",
            result.stdout,
        )

    def test_frozen_holdout_v1_files_match_manifest(self):
        result = subprocess.run(
            [
                sys.executable,
                "benchmark/holdout/"
                "verify_v1_integrity.py",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=(
                result.stdout
                + result.stderr
            ),
        )

        self.assertIn(
            "Holdout v1 integrity check passed.",
            result.stdout,
        )


if __name__ == "__main__":
    unittest.main()
