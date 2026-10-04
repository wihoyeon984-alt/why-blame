import unittest

from claim_predicate import (
    PREDICATE_AND,
    PREDICATE_IS_FALSE,
    PREDICATE_IS_TRUE,
    PREDICATE_NAME,
    PREDICATE_NOT,
    PREDICATE_OR,
    collect_predicate_names,
    extract_condition_predicate,
)


class TestClaimPredicate(unittest.TestCase):

    def test_simple_name_condition(self):
        result = extract_condition_predicate(
            "if enabled:"
        )

        self.assertEqual(
            result,
            {
                "op": PREDICATE_NAME,
                "name": "enabled",
            },
        )

    def test_not_condition(self):
        result = extract_condition_predicate(
            "if not enabled:"
        )

        self.assertEqual(
            result,
            {
                "op": PREDICATE_NOT,
                "operand": {
                    "op": PREDICATE_NAME,
                    "name": "enabled",
                },
            },
        )

    def test_is_true_condition(self):
        result = extract_condition_predicate(
            "if verify is True:"
        )

        self.assertEqual(
            result,
            {
                "op": PREDICATE_IS_TRUE,
                "name": "verify",
            },
        )

    def test_is_false_condition(self):
        result = extract_condition_predicate(
            "if verify is False:"
        )

        self.assertEqual(
            result,
            {
                "op": PREDICATE_IS_FALSE,
                "name": "verify",
            },
        )

    def test_and_condition(self):
        result = extract_condition_predicate(
            (
                "if verify is True and "
                "not has_poolmanager_ssl_context:"
            )
        )

        self.assertEqual(
            result["op"],
            PREDICATE_AND,
        )

        self.assertEqual(
            result["values"][0],
            {
                "op": PREDICATE_IS_TRUE,
                "name": "verify",
            },
        )

        self.assertEqual(
            result["values"][1],
            {
                "op": PREDICATE_NOT,
                "operand": {
                    "op": PREDICATE_NAME,
                    "name": (
                        "has_poolmanager_ssl_context"
                    ),
                },
            },
        )

    def test_elif_is_normalized_as_if_condition(self):
        result = extract_condition_predicate(
            (
                "elif verify is True and "
                "not has_poolmanager_ssl_context:"
            )
        )

        self.assertEqual(
            result["op"],
            PREDICATE_AND,
        )

        names = collect_predicate_names(
            result
        )

        self.assertEqual(
            names,
            [
                "verify",
                "has_poolmanager_ssl_context",
            ],
        )

    def test_or_condition(self):
        result = extract_condition_predicate(
            "if cached or fallback:"
        )

        self.assertEqual(
            result["op"],
            PREDICATE_OR,
        )

        self.assertEqual(
            collect_predicate_names(
                result
            ),
            [
                "cached",
                "fallback",
            ],
        )

    def test_attribute_name_is_preserved(self):
        result = extract_condition_predicate(
            "if request.is_secure:"
        )

        self.assertEqual(
            result,
            {
                "op": PREDICATE_NAME,
                "name": "request.is_secure",
            },
        )

    def test_unsupported_comparison_is_not_guessed(self):
        result = extract_condition_predicate(
            "if count > 10:"
        )

        self.assertIsNone(
            result
        )

    def test_function_call_condition_is_not_guessed(self):
        result = extract_condition_predicate(
            "if has_context():"
        )

        self.assertIsNone(
            result
        )

    def test_invalid_condition_is_not_guessed(self):
        result = extract_condition_predicate(
            "if value is:"
        )

        self.assertIsNone(
            result
        )

    def test_non_condition_statement_is_ignored(self):
        result = extract_condition_predicate(
            'o = o.encode("utf-8")'
        )

        self.assertIsNone(
            result
        )

    def test_predicate_names_do_not_infer_meaning(self):
        result = extract_condition_predicate(
            (
                "if verify is True and "
                "not has_poolmanager_ssl_context:"
            )
        )

        names = collect_predicate_names(
            result
        )

        self.assertIn(
            "verify",
            names,
        )

        self.assertIn(
            "has_poolmanager_ssl_context",
            names,
        )

        self.assertNotIn(
            "custom SSLContext",
            names,
        )

        self.assertNotIn(
            "default SSLContext",
            names,
        )


if __name__ == "__main__":
    unittest.main()