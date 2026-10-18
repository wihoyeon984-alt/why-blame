import unittest

from webapp.i18n import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    TEXT,
    translate,
)


class WebappI18nTests(unittest.TestCase):
    def test_supported_languages_include_english_and_korean(self):
        self.assertEqual(DEFAULT_LANGUAGE, "en")
        self.assertEqual(
            SUPPORTED_LANGUAGES,
            {
                "en": "English",
                "ko": "한국어",
            },
        )

    def test_all_languages_have_the_same_translation_keys(self):
        expected_keys = set(TEXT[DEFAULT_LANGUAGE])

        for language, translations in TEXT.items():
            with self.subTest(language=language):
                self.assertEqual(
                    set(translations),
                    expected_keys,
                )

    def test_translate_returns_requested_language(self):
        self.assertEqual(
            translate("en", "start_analysis"),
            "Start analysis",
        )
        self.assertEqual(
            translate("ko", "start_analysis"),
            "분석 시작",
        )

    def test_translate_formats_placeholder_values(self):
        self.assertEqual(
            translate("en", "evidence_event", index=3),
            "Evidence event 3",
        )
        self.assertEqual(
            translate("ko", "evidence_event", index=3),
            "근거 이벤트 3",
        )

    def test_unknown_language_falls_back_to_english(self):
        self.assertEqual(
            translate("unknown", "raw_json"),
            "Raw JSON",
        )

    def test_unknown_translation_key_raises_key_error(self):
        with self.assertRaises(KeyError):
            translate("en", "missing-key")


if __name__ == "__main__":
    unittest.main()
