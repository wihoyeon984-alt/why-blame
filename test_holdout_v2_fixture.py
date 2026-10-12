import subprocess
import sys
import unittest
from pathlib import Path


class TestHoldoutV2Fixture(unittest.TestCase):

    def test_fixture_scores_end_to_end(self):
        result = subprocess.run(
            [
                sys.executable,
                str(
                    Path(
                        "benchmark/holdout_v2/"
                        "score_holdout_v2.py"
                    )
                ),
                "--cases-dir",
                str(
                    Path(
                        "benchmark/holdout_v2/"
                        "fixtures/cases"
                    )
                ),
                "--scoring-dir",
                str(
                    Path(
                        "benchmark/holdout_v2/"
                        "fixtures/scoring"
                    )
                ),
            ],
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
            "VERY_HIGH",
            result.stdout,
        )
        self.assertIn(
            "Cases:                     1",
            result.stdout,
        )
        self.assertIn(
            "Claim precision:           1.000",
            result.stdout,
        )
        self.assertIn(
            "Supported recall:          0.500",
            result.stdout,
        )
        self.assertIn(
            "Unsafe presentation rate:  0.000",
            result.stdout,
        )


if __name__ == "__main__":
    unittest.main()
