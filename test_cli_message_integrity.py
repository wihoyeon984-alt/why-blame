import unittest
from pathlib import Path

from main import parse_output_mode


DUPLICATE_JSON_MESSAGE = (
    "--json \uc635\uc158\uc740 \ud55c \ubc88\ub9cc "
    "\uc9c0\uc815\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4."
)

JSON_CONFLICT_MESSAGE = (
    "--json \uc635\uc158\uc740 --help \ub610\ub294 "
    "--version \uc635\uc158\uacfc "
    "\ud568\uaed8 \uc0ac\uc6a9\ud560 \uc218 "
    "\uc5c6\uc2b5\ub2c8\ub2e4."
)


class CliMessageIntegrityTests(unittest.TestCase):
    def test_duplicate_json_option_has_readable_error(self):
        with self.assertRaises(ValueError) as context:
            parse_output_mode(
                [
                    "service.py:1",
                    "--json",
                    "--json",
                ]
            )

        self.assertEqual(
            str(context.exception),
            DUPLICATE_JSON_MESSAGE,
        )

    def test_json_cannot_be_combined_with_help(self):
        with self.assertRaises(ValueError) as context:
            parse_output_mode(
                [
                    "--help",
                    "--json",
                ]
            )

        self.assertEqual(
            str(context.exception),
            JSON_CONFLICT_MESSAGE,
        )

    def test_json_cannot_be_combined_with_version(self):
        with self.assertRaises(ValueError) as context:
            parse_output_mode(
                [
                    "--version",
                    "--json",
                ]
            )

        self.assertEqual(
            str(context.exception),
            JSON_CONFLICT_MESSAGE,
        )

    def test_main_source_has_no_corrupted_user_messages(self):
        text = Path("main.py").read_text(encoding="utf-8")

        corrupted_message = "?" * 3
        corrupted_prefix = "?" * 2 + ":"

        self.assertNotIn(corrupted_message, text)
        self.assertNotIn(corrupted_prefix, text)
        self.assertNotIn("\ufffd", text)


if __name__ == "__main__":
    unittest.main()
