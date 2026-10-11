import unittest

from claim_predicate import (
    PREDICATE_AND,
    PREDICATE_IS_TRUE,
    PREDICATE_NAME,
    PREDICATE_NOT,
    PREDICATE_OR,
)
from claim_predicate_diff import (
    DELTA_KNOWN,
    DELTA_UNKNOWN,
    compare_predicates,
    predicate_delta_from_code,
)


class TestClaimPredicateDiff(
    unittest.TestCase
):

    def test_added_and_condition_is_detected(self):
        old = {
            "op": PREDICATE_IS_TRUE,
            "name": "verify",
        }

        new = {
            "op": PREDICATE_AND,
            "values": [
                {
                    "op": PREDICATE_IS_TRUE,
                    "name": "verify",
                },
                {
                    "op": PREDICATE_NOT,
                    "operand": {
                        "op": PREDICATE_NAME,
                        "name": (
                            "has_poolmanager_ssl_context"
                        ),
                    },
                },
            ],
        }

        result = compare_predicates(
            old,
            new,
        )

        self.assertEqual(
            result["status"],
            DELTA_KNOWN,
        )

        self.assertEqual(
            result["preserved"],
            [
                {
                    "op": PREDICATE_IS_TRUE,
                    "name": "verify",
                }
            ],
        )

        self.assertEqual(
            result["added"],
            [
                {
                    "op": PREDICATE_NOT,
                    "operand": {
                        "op": PREDICATE_NAME,
                        "name": (
                            "has_poolmanager_ssl_context"
                        ),
                    },
                }
            ],
        )

        self.assertEqual(
            result["removed"],
            [],
        )

    def test_removed_condition_is_detected(self):
        old = {
            "op": PREDICATE_AND,
            "values": [
                {
                    "op": PREDICATE_NAME,
                    "name": "enabled",
                },
                {
                    "op": PREDICATE_NAME,
                    "name": "authorized",
                },
            ],
        }

        new = {
            "op": PREDICATE_NAME,
            "name": "enabled",
        }

        result = compare_predicates(
            old,
            new,
        )

        self.assertEqual(
            result["preserved"],
            [
                {
                    "op": PREDICATE_NAME,
                    "name": "enabled",
                }
            ],
        )

        self.assertEqual(
            result["removed"],
            [
                {
                    "op": PREDICATE_NAME,
                    "name": "authorized",
                }
            ],
        )

        self.assertEqual(
            result["added"],
            [],
        )

    def test_unchanged_predicate_is_preserved(self):
        old = {
            "op": PREDICATE_NAME,
            "name": "enabled",
        }

        new = {
            "op": PREDICATE_NAME,
            "name": "enabled",
        }

        result = compare_predicates(
            old,
            new,
        )

        self.assertEqual(
            len(result["preserved"]),
            1,
        )

        self.assertEqual(
            result["added"],
            [],
        )

        self.assertEqual(
            result["removed"],
            [],
        )

    def test_changed_predicate_is_remove_plus_add(self):
        old = {
            "op": PREDICATE_NAME,
            "name": "enabled",
        }

        new = {
            "op": PREDICATE_NOT,
            "operand": {
                "op": PREDICATE_NAME,
                "name": "enabled",
            },
        }

        result = compare_predicates(
            old,
            new,
        )

        self.assertEqual(
            result["preserved"],
            [],
        )

        self.assertEqual(
            len(result["removed"]),
            1,
        )

        self.assertEqual(
            len(result["added"]),
            1,
        )

    def test_requests_style_code_delta_is_structural_only(self):
        result = predicate_delta_from_code(
            "elif verify is True:",
            (
                "elif verify is True and not "
                "has_poolmanager_ssl_context:"
            ),
        )

        self.assertEqual(
            result["status"],
            DELTA_KNOWN,
        )

        self.assertEqual(
            result["preserved"],
            [
                {
                    "op": PREDICATE_IS_TRUE,
                    "name": "verify",
                }
            ],
        )

        self.assertEqual(
            result["added"],
            [
                {
                    "op": PREDICATE_NOT,
                    "operand": {
                        "op": PREDICATE_NAME,
                        "name": (
                            "has_poolmanager_ssl_context"
                        ),
                    },
                }
            ],
        )

    def test_delta_does_not_infer_sslcontext_meaning(self):
        result = predicate_delta_from_code(
            "elif verify is True:",
            (
                "elif verify is True and not "
                "has_poolmanager_ssl_context:"
            ),
        )

        text = repr(result)

        self.assertNotIn(
            "custom SSLContext",
            text,
        )

        self.assertNotIn(
            "default SSLContext",
            text,
        )

        self.assertNotIn(
            "compatibility",
            text.lower(),
        )

    def test_unknown_old_code_makes_delta_unknown(self):
        result = predicate_delta_from_code(
            "if count > 10:",
            "if enabled:",
        )

        self.assertEqual(
            result["status"],
            DELTA_UNKNOWN,
        )

        self.assertEqual(
            result["preserved"],
            [],
        )

        self.assertEqual(
            result["added"],
            [],
        )

        self.assertEqual(
            result["removed"],
            [],
        )

    def test_unknown_new_code_makes_delta_unknown(self):
        result = predicate_delta_from_code(
            "if enabled:",
            "if has_context():",
        )

        self.assertEqual(
            result["status"],
            DELTA_UNKNOWN,
        )

    def test_and_reordering_is_structurally_preserved(self):
        old = {
            "op": PREDICATE_AND,
            "values": [
                {
                    "op": PREDICATE_NAME,
                    "name": "enabled",
                },
                {
                    "op": PREDICATE_NAME,
                    "name": "authorized",
                },
            ],
        }

        new = {
            "op": PREDICATE_AND,
            "values": [
                {
                    "op": PREDICATE_NAME,
                    "name": "authorized",
                },
                {
                    "op": PREDICATE_NAME,
                    "name": "enabled",
                },
            ],
        }

        result = compare_predicates(
            old,
            new,
        )

        self.assertEqual(
            result["status"],
            DELTA_KNOWN,
        )

        self.assertEqual(
            len(result["preserved"]),
            2,
        )

        self.assertEqual(
            result["added"],
            [],
        )

        self.assertEqual(
            result["removed"],
            [],
        )

    def test_or_terms_are_compared_without_semantic_rewrite(self):
        old = {
            "op": PREDICATE_OR,
            "values": [
                {
                    "op": PREDICATE_NAME,
                    "name": "cached",
                },
                {
                    "op": PREDICATE_NAME,
                    "name": "fallback",
                },
            ],
        }

        new = {
            "op": PREDICATE_OR,
            "values": [
                {
                    "op": PREDICATE_NAME,
                    "name": "cached",
                },
                {
                    "op": PREDICATE_NAME,
                    "name": "fresh",
                },
            ],
        }

        result = compare_predicates(
            old,
            new,
        )

        self.assertEqual(
            len(result["preserved"]),
            1,
        )

        self.assertEqual(
            len(result["added"]),
            1,
        )

        self.assertEqual(
            len(result["removed"]),
            1,
        )


if __name__ == "__main__":
    unittest.main()