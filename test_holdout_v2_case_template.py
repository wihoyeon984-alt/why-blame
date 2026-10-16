import unittest
from pathlib import Path

from benchmark.holdout_v2.case import (
    load_case,
)


class TestHoldoutV2CaseTemplate(unittest.TestCase):

    def test_case_template_is_valid(self):
        case = load_case(
            Path(
                "benchmark/holdout_v2/"
                "CASE_TEMPLATE.json"
            )
        )

        self.assertEqual(
            case.schema_version,
            2,
        )
        self.assertTrue(case.frozen)
        self.assertGreaterEqual(
            len(case.claims),
            1,
        )
        self.assertTrue(
            case.repository_url.startswith(
                "https://"
            )
        )


if __name__ == "__main__":
    unittest.main()
