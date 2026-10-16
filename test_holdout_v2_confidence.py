import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent

MODULE_PATH = (
    ROOT
    / "benchmark"
    / "holdout_v2"
    / "confidence.py"
)

SPEC = importlib.util.spec_from_file_location(
    "holdout_v2_confidence",
    MODULE_PATH,
)

confidence = importlib.util.module_from_spec(
    SPEC
)

assert SPEC.loader is not None

sys.modules[SPEC.name] = confidence
SPEC.loader.exec_module(confidence)


class TestHoldoutV2Confidence(unittest.TestCase):

    def test_normalizes_display_labels(self):
        self.assertEqual(
            confidence.normalize_confidence(
                "VERY HIGH"
            ),
            "VERY_HIGH",
        )

        self.assertEqual(
            confidence.normalize_confidence(
                "very weak"
            ),
            "VERY_WEAK",
        )

    def test_preserves_normalized_labels(self):
        self.assertEqual(
            confidence.normalize_confidence(
                "MEDIUM"
            ),
            "MEDIUM",
        )

    def test_unknown_value_is_conservative(self):
        self.assertEqual(
            confidence.normalize_confidence(
                "VERY"
            ),
            "UNKNOWN",
        )

        self.assertEqual(
            confidence.normalize_confidence(
                None
            ),
            "UNKNOWN",
        )


if __name__ == "__main__":
    unittest.main()
