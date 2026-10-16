import json
import unittest
from pathlib import Path


class TestHoldoutV2Schema(unittest.TestCase):

    def test_scoring_template_has_required_fields(self):
        path = Path(
            "benchmark/holdout_v2/"
            "SCORING_TEMPLATE.json"
        )

        data = json.loads(
            path.read_text(encoding="utf-8")
        )

        self.assertEqual(
            data["schema_version"],
            2,
        )
        self.assertIsInstance(
            data["case_id"],
            str,
        )
        self.assertIn(
            "completed",
            data["execution"],
        )
        self.assertIn(
            "level",
            data["confidence"],
        )
        self.assertIn(
            "source",
            data["confidence"],
        )
        self.assertIsInstance(
            data["claims"],
            dict,
        )


if __name__ == "__main__":
    unittest.main()
