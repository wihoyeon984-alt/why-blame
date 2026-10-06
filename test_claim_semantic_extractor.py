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
    extract_direct_local_helper_semantics,
    extract_statement_semantics,
    extract_target_semantics,
    find_direct_local_helpers,
    extract_statement_ordering,
    extract_target_ordering,
    derive_transitive_ordering,
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


    def test_direct_local_helper_is_bounded_expansion_candidate(self):
        source = 'def helper(value):\n    return value\n\ndef caller(value):\n    return helper(value)'
        result = find_direct_local_helpers(source, 'return helper(value)')
        self.assertEqual(result, ['helper'])

    def test_bounded_expansion_does_not_follow_nested_helper(self):
        source = 'def nested_helper(value):\n    return value\n\ndef helper(value):\n    return nested_helper(value)\n\ndef caller(value):\n    return helper(value)'
        result = find_direct_local_helpers(source, 'return helper(value)')
        self.assertEqual(result, ['helper'])

    def test_attribute_call_is_not_treated_as_local_helper(self):
        source = 'def helper(value):\n    return value'
        result = find_direct_local_helpers(source, 'return service.helper(value)')
        self.assertEqual(result, [])


    def test_direct_local_helper_body_yields_structured_semantics(self):
        source = (
            'def helper(value):\n'
            '    value = value.encode("utf-8")\n'
            '\n'
            'def caller(value):\n'
            '    helper(value)\n'
        )

        result = extract_direct_local_helper_semantics(
            source,
            'helper(value)',
            "abc123",
        )

        self.assertEqual(
            len(result),
            1,
        )
        self.assertEqual(
            result[0]["action"],
            "ENCODE",
        )
        self.assertEqual(
            result[0]["subject"],
            "value",
        )
        self.assertEqual(
            result[0]["target"],
            "UTF-8",
        )
        self.assertEqual(
            result[0]["source_event"],
            "abc123",
        )



    def test_direct_local_helper_preserves_direct_condition(self):
        source = (
            'def helper(value):\n'
            '    if value:\n'
            '        value = value.encode("utf-8")\n'
            '\n'
            'def caller(value):\n'
            '    helper(value)\n'
        )

        result = extract_direct_local_helper_semantics(
            source,
            'helper(value)',
            "abc123",
        )

        self.assertEqual(
            len(result),
            1,
        )
        self.assertEqual(
            result[0]["action"],
            "ENCODE",
        )
        self.assertEqual(
            result[0]["subject"],
            "value",
        )
        self.assertEqual(
            result[0]["target"],
            "UTF-8",
        )
        self.assertEqual(
            result[0]["condition"],
            "value",
        )
        self.assertEqual(
            result[0]["field_evidence"]["condition"][0]["level"],
            "DIRECT",
        )
        self.assertEqual(
            result[0]["source_event"],
            "abc123",
        )

    def test_helper_semantics_do_not_expand_to_nested_helper(self):
        source = (
            'def nested_helper(value):\n'
            '    value = value.encode("utf-8")\n'
            '\n'
            'def helper(value):\n'
            '    nested_helper(value)\n'
            '\n'
            'def caller(value):\n'
            '    helper(value)\n'
        )

        result = extract_direct_local_helper_semantics(
            source,
            'helper(value)',
            "abc123",
        )

        self.assertEqual(
            result,
            [],
        )


    def test_target_semantics_expand_direct_local_helper(self):
        source = (
            'def helper(value):\n'
            '    value = value.encode("utf-8")\n'
            '\n'
            'def caller(value):\n'
            '    helper(value)\n'
        )

        timeline = [
            {
                "hash": "abc123",
                "diff_lines": [
                    "+ helper(value)",
                ],
                "source": source,
            }
        ]

        result = extract_target_semantics(
            timeline
        )

        self.assertEqual(
            len(result),
            1,
        )
        self.assertEqual(
            result[0]["action"],
            "ENCODE",
        )
        self.assertEqual(
            result[0]["subject"],
            "value",
        )
        self.assertEqual(
            result[0]["target"],
            "UTF-8",
        )
        self.assertEqual(
            result[0]["source_event"],
            "abc123",
        )


    def test_target_semantics_do_not_expand_nested_helper(self):
        source = (
            'def nested_helper(value):\n'
            '    value = value.encode("utf-8")\n'
            '\n'
            'def helper(value):\n'
            '    nested_helper(value)\n'
            '\n'
            'def caller(value):\n'
            '    helper(value)\n'
        )

        timeline = [
            {
                "hash": "abc123",
                "diff_lines": [
                    "+ helper(value)",
                ],
                "source": source,
            }
        ]

        result = extract_target_semantics(
            timeline
        )

        self.assertEqual(
            result,
            [],
        )


    def test_statement_ordering_preserves_direct_call_sequence(self):
        code = (
            'sock = create_socket()\n'
            'cleanup.append(sock)\n'
            'sock.bind(address)\n'
        )

        result = extract_statement_ordering(
            code,
            "abc123",
        )

        self.assertEqual(
            result,
            [
                {
                    "before": "create_socket()",
                    "after": "cleanup.append(sock)",
                    "source_event": "abc123",
                },
                {
                    "before": "cleanup.append(sock)",
                    "after": "sock.bind(address)",
                    "source_event": "abc123",
                },
            ],
        )




    def test_statement_ordering_preserves_for_body_inside_try(self):
        code = (
            'try:\n'
            '    for item in items:\n'
            '        sock = create_socket()\n'
            '        cleanup.append(sock)\n'
            '        sock.configure()\n'
            '        sock.bind(address)\n'
            'except Exception:\n'
            '    cleanup_failed()\n'
        )

        result = extract_statement_ordering(
            code,
            "abc123",
        )

        self.assertEqual(
            result,
            [
                {
                    "before": "create_socket()",
                    "after": "cleanup.append(sock)",
                    "source_event": "abc123",
                },
                {
                    "before": "cleanup.append(sock)",
                    "after": "sock.configure()",
                    "source_event": "abc123",
                },
                {
                    "before": "sock.configure()",
                    "after": "sock.bind(address)",
                    "source_event": "abc123",
                },
            ],
        )

    def test_statement_ordering_preserves_sequence_inside_for_body(self):
        code = (
            'for item in items:\n'
            '    sock = create_socket()\n'
            '    cleanup.append(sock)\n'
            '    sock.configure()\n'
            '    sock.bind(address)\n'
        )

        result = extract_statement_ordering(
            code,
            "abc123",
        )

        self.assertEqual(
            result,
            [
                {
                    "before": "create_socket()",
                    "after": "cleanup.append(sock)",
                    "source_event": "abc123",
                },
                {
                    "before": "cleanup.append(sock)",
                    "after": "sock.configure()",
                    "source_event": "abc123",
                },
                {
                    "before": "sock.configure()",
                    "after": "sock.bind(address)",
                    "source_event": "abc123",
                },
            ],
        )

    def test_statement_ordering_does_not_cross_nested_control_flow(self):
        code = (
            'sock = create_socket()\n'
            'if should_track:\n'
            '    cleanup.append(sock)\n'
            'sock.bind(address)\n'
        )

        result = extract_statement_ordering(
            code,
            "abc123",
        )

        self.assertEqual(
            result,
            [
                {
                    "before": "create_socket()",
                    "after": "sock.bind(address)",
                    "source_event": "abc123",
                },
            ],
        )



    def test_transitive_ordering_preserves_precedes_relation(self):
        ordering = [
            {
                "before": "create_socket()",
                "after": "cleanup.append(sock)",
                "source_event": "abc123",
            },
            {
                "before": "cleanup.append(sock)",
                "after": "sock.configure()",
                "source_event": "abc123",
            },
            {
                "before": "sock.configure()",
                "after": "sock.bind(address)",
                "source_event": "abc123",
            },
        ]

        result = derive_transitive_ordering(
            ordering
        )

        self.assertIn(
            {
                "before": "cleanup.append(sock)",
                "after": "sock.bind(address)",
                "source_event": "abc123",
            },
            result,
        )


    def test_transitive_ordering_does_not_cross_source_events(self):
        ordering = [
            {
                "before": "operation_a()",
                "after": "operation_b()",
                "source_event": "event_a",
            },
            {
                "before": "operation_b()",
                "after": "operation_c()",
                "source_event": "event_b",
            },
        ]

        result = derive_transitive_ordering(
            ordering
        )

        self.assertNotIn(
            {
                "before": "operation_a()",
                "after": "operation_c()",
                "source_event": "event_a",
            },
            result,
        )


    def test_transitive_ordering_closes_longer_chain(self):
        ordering = [
            {
                "before": "operation_a()",
                "after": "operation_b()",
                "source_event": "abc123",
            },
            {
                "before": "operation_b()",
                "after": "operation_c()",
                "source_event": "abc123",
            },
            {
                "before": "operation_c()",
                "after": "operation_d()",
                "source_event": "abc123",
            },
        ]

        result = derive_transitive_ordering(
            ordering
        )

        self.assertIn(
            {
                "before": "operation_a()",
                "after": "operation_d()",
                "source_event": "abc123",
            },
            result,
        )

    def test_target_ordering_uses_only_final_event(self):
        timeline = [
            {
                "hash": "old123",
                "source": (
                    'old_sock = old_socket()\n'
                    'old_sock.bind(old_address)\n'
                ),
            },
            {
                "hash": "abc123",
                "source": (
                    'sock = create_socket()\n'
                    'cleanup.append(sock)\n'
                    'sock.bind(address)\n'
                ),
            },
        ]

        result = extract_target_ordering(
            timeline
        )

        self.assertEqual(
            result,
            [
                {
                    "before": "create_socket()",
                    "after": "cleanup.append(sock)",
                    "source_event": "abc123",
                },
                {
                    "before": "cleanup.append(sock)",
                    "after": "sock.bind(address)",
                    "source_event": "abc123",
                },
            ],
        )

if __name__ == "__main__":
    unittest.main()
