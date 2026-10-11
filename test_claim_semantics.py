import unittest

from claim_semantics import (
    BEHAVIOR,
    DIRECT,
    NONE,
    attach_field_evidence,
    get_field_evidence,
    get_present_fields,
    make_behavior_semantics,
)


class TestClaimSemantics(unittest.TestCase):

    def test_behavior_semantics_has_explicit_fields(self):
        semantics = make_behavior_semantics(
            action="AVOID",
            subject="default SSLContext",
            condition="custom SSLContext exists",
            target="poolmanager",
            source_event="abc123",
        )

        self.assertEqual(
            semantics["type"],
            BEHAVIOR,
        )

        self.assertEqual(
            semantics["action"],
            "AVOID",
        )

        self.assertEqual(
            semantics["subject"],
            "default SSLContext",
        )

        self.assertEqual(
            semantics["condition"],
            "custom SSLContext exists",
        )

        self.assertEqual(
            semantics["target"],
            "poolmanager",
        )

        self.assertEqual(
            semantics["source_event"],
            "abc123",
        )

        self.assertEqual(
            semantics["entailment"],
            NONE,
        )

    def test_present_fields_only_include_values(self):
        semantics = make_behavior_semantics(
            action="ENCODE",
            subject="string input",
            target="UTF-8",
            source_event="3fd309a5",
        )

        fields = get_present_fields(
            semantics
        )

        self.assertEqual(
            fields,
            [
                "action",
                "subject",
                "target",
            ],
        )

    def test_field_evidence_is_attached_explicitly(self):
        semantics = make_behavior_semantics(
            action="ENCODE",
            subject="string input",
            target="UTF-8",
            source_event="3fd309a5",
        )

        result = attach_field_evidence(
            semantics,
            "action",
            source="DIFF",
            ref="3fd309a5",
            level=DIRECT,
        )

        evidence = get_field_evidence(
            result,
            "action",
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
            "3fd309a5",
        )

        self.assertEqual(
            evidence[0]["level"],
            DIRECT,
        )

    def test_attaching_evidence_does_not_mutate_original(self):
        original = make_behavior_semantics(
            action="ENCODE",
            subject="string input",
            source_event="3fd309a5",
        )

        updated = attach_field_evidence(
            original,
            "action",
            source="DIFF",
            ref="3fd309a5",
            level=DIRECT,
        )

        self.assertEqual(
            get_field_evidence(
                original,
                "action",
            ),
            [],
        )

        self.assertEqual(
            len(
                get_field_evidence(
                    updated,
                    "action",
                )
            ),
            1,
        )

    def test_unknown_field_is_rejected(self):
        semantics = make_behavior_semantics(
            action="ENCODE",
            source_event="abc123",
        )

        with self.assertRaises(
            ValueError
        ):
            attach_field_evidence(
                semantics,
                "reason",
                source="PR",
                ref="#1",
                level=DIRECT,
            )


if __name__ == "__main__":
    unittest.main()
