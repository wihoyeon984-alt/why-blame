from claim_adapter import build_behavior_claims
from claim_safe_renderer import render_safe_semantics
from claim_safety import with_semantic_safety
from webapp.beginner_behavior import (
    build_beginner_behavior_contract,
)


def _copy_explicit_evidence(semantics):
    copied = dict(semantics)
    field_evidence = semantics.get("field_evidence", {})

    if isinstance(field_evidence, dict):
        copied["field_evidence"] = {
            field: [
                dict(item)
                for item in items
                if isinstance(item, dict)
            ]
            for field, items in field_evidence.items()
            if isinstance(items, (list, tuple))
        }

    return copied


def build_beginner_behavior_from_analysis(
    timeline,
    current_lines,
    stats,
):
    claims = build_behavior_claims(timeline)
    structured_claims = []

    for claim in claims:
        if claim.get("type") != "BEHAVIOR":
            continue

        evidence_items = claim.get("evidence", [])
        semantics_items = claim.get(
            "structured_semantics",
            [],
        )

        for semantics in semantics_items:
            if not isinstance(semantics, dict):
                continue

            evaluated = with_semantic_safety(
                semantics,
                evidence_items,
            )
            safe_statement = render_safe_semantics(
                evaluated
            )

            converted = {
                "type": claim.get("type"),
                "target_relevant": claim.get(
                    "target_relevant"
                ),
                "source_event": claim.get(
                    "source_event"
                ),
                "structured_semantics": [
                    _copy_explicit_evidence(evaluated)
                ],
                "semantic_safety": evaluated.get(
                    "semantic_safety"
                ),
            }

            if safe_statement:
                converted["safe_statement"] = safe_statement

            structured_claims.append(converted)

    return build_beginner_behavior_contract(
        current_lines,
        structured_claims,
        stats,
    )
