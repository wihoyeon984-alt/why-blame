import unittest

from claim_entailment import (
    evaluate_semantic_entailment,
)
from claim_safe_renderer import (
    render_safe_semantics,
)
from claim_safety import (
    SAFE_TO_RENDER,
    with_semantic_safety,
)
from claim_semantic_extractor import (
    extract_diff_semantics,
    extract_statement_semantics,
    extract_target_semantics,
)
from claim_semantics import (
    DIRECT,
)


class TestClaimSemanticExtractor(
    unittest.TestCase
):

    def test_encode_assignment_extracts_structured_semantics(self):
        result = extract_statement_semantics(
            'o = o.encode("utf-8")',
            "abc123",
        )

        self.assertEqual(
            len(result),
            1,
        )

        semantics = result[0]

        self.assertEqual(
            semantics["action"],
            "ENCODE",
        )

        self.assertEqual(
            semantics["subject"],
            "o",
        )

        self.assertEqual(
            semantics["target"],
            "UTF-8",
        )

        self.assertEqual(
            semantics["source_event"],
            "abc123",
        )

    def test_extracted_fields_have_direct_diff_evidence(self):
        result = extract_statement_semantics(
            'o = o.encode("utf-8")',
            "abc123",
        )

        semantics = result[0]

        for field in (
            "action",
            "subject",
            "target",
        ):
            evidence = (
                semantics[
                    "field_evidence"
                ][field]
            )

            self.assertEqual(
                len(evidence),
                1,
            )

            self.assertEqual(
                evidence[0]["source"],
                "DIFF",
            )

            self.assertEqual(
                evidence[0]["ref"],
                "abc123",
            )

            self.assertEqual(
                evidence[0]["level"],
                DIRECT,
            )

    def test_encode_semantics_are_directly_entailed(self):
        result = extract_statement_semantics(
            'o = o.encode("utf-8")',
            "abc123",
        )

        semantics = result[0]

        entailment = (
            evaluate_semantic_entailment(
                semantics
            )
        )

        self.assertEqual(
            entailment,
            DIRECT,
        )

    def test_encode_semantics_flow_through_safety_and_renderer(self):
        result = extract_statement_semantics(
            'o = o.encode("utf-8")',
            "abc123",
        )

        semantics = with_semantic_safety(
            result[0],
            [],
        )

        self.assertEqual(
            semantics["semantic_safety"],
            SAFE_TO_RENDER,
        )

        rendered = render_safe_semantics(
            semantics
        )

        self.assertEqual(
            rendered,
            "o is encoded as UTF-8.",
        )

    def test_deleted_diff_is_not_extracted(self):
        result = extract_diff_semantics(
            [
                '- o = o.encode("utf-8")',
            ],
            "abc123",
        )

        self.assertEqual(
            result,
            [],
        )

    def test_unknown_statement_is_not_guessed(self):
        result = extract_statement_semantics(
            "custom_operation(value)",
            "abc123",
        )

        self.assertEqual(
            result,
            [],
        )

    def test_invalid_python_is_not_guessed(self):
        result = extract_statement_semantics(
            "if value is:",
            "abc123",
        )

        self.assertEqual(
            result,
            [],
        )

    def test_encode_of_different_variable_is_not_assumed(self):
        result = extract_statement_semantics(
            'result = value.encode("utf-8")',
            "abc123",
        )

        self.assertEqual(
            result,
            [],
        )

    def test_historical_event_is_not_target_semantics(self):
        timeline = [
            {
                "hash": "old111",
                "diff_lines": [
                    '+ old = old.encode("utf-8")',
                ],
            },
            {
                "hash": "new222",
                "diff_lines": [
                    '+ current = current.encode("utf-8")',
                ],
            },
        ]

        result = extract_target_semantics(
            timeline
        )

        self.assertEqual(
            len(result),
            1,
        )

        self.assertEqual(
            result[0]["subject"],
            "current",
        )

        self.assertEqual(
            result[0]["source_event"],
            "new222",
        )

    def test_empty_timeline_returns_no_semantics(self):
        result = extract_target_semantics(
            []
        )

        self.assertEqual(
            result,
            [],
        )


if __name__ == "__main__":
    unittest.main()