import unittest

from webapp.i18n import translate_error
from webapp.runner import DashboardRunError
from webapp.validators import ValidationError


class WebappErrorI18nTests(unittest.TestCase):
    def test_validation_error_preserves_message_and_code(self):
        error = ValidationError(
            "The requested file does not exist.",
            code="FILE_NOT_FOUND",
        )

        self.assertEqual(str(error), "The requested file does not exist.")
        self.assertEqual(error.code, "FILE_NOT_FOUND")

    def test_runner_error_preserves_message_and_code(self):
        error = DashboardRunError(
            "Why-Blame analysis timed out.",
            code="ANALYSIS_TIMEOUT",
        )

        self.assertEqual(str(error), "Why-Blame analysis timed out.")
        self.assertEqual(error.code, "ANALYSIS_TIMEOUT")

    def test_translates_file_not_found_in_both_languages(self):
        error = ValidationError(
            "The requested file does not exist.",
            code="FILE_NOT_FOUND",
        )

        self.assertEqual(
            translate_error("en", error),
            "The requested file does not exist.",
        )
        self.assertEqual(
            translate_error("ko", error),
            "요청한 파일이 존재하지 않습니다.",
        )

    def test_translates_timeout_in_both_languages(self):
        error = DashboardRunError(
            "Why-Blame analysis timed out.",
            code="ANALYSIS_TIMEOUT",
        )

        self.assertEqual(
            translate_error("en", error),
            "Why-Blame analysis timed out.",
        )
        self.assertEqual(
            translate_error("ko", error),
            "Why-Blame 분석 시간이 제한을 초과했습니다.",
        )

    def test_unknown_code_preserves_original_message(self):
        error = ValidationError(
            "Original diagnostic.",
            code="UNKNOWN_ERROR",
        )

        self.assertEqual(
            translate_error("ko", error),
            "Original diagnostic.",
        )

    def test_uncoded_error_preserves_original_message(self):
        error = ValueError("Original diagnostic.")

        self.assertEqual(
            translate_error("ko", error),
            "Original diagnostic.",
        )


if __name__ == "__main__":
    unittest.main()
