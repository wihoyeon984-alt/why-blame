from webapp.i18n import translate


def _enum_value(value):
    return getattr(value, "value", value)


def _translated_code(language, code, prefix):
    key = prefix + _enum_value(code)
    try:
        return translate(language, key)
    except KeyError:
        return translate(language, "easy_unknown_information")


def build_easy_explanation_sections(beginner_evidence, language):
    """Build safe, localized display data from the evidence contract only."""
    if beginner_evidence is None:
        return {
            "available": False,
            "fallback": translate(language, "easy_explanation_fallback"),
        }

    reason_status = _enum_value(
        getattr(beginner_evidence, "reason_status", None)
    )
    evidence_items = getattr(
        beginner_evidence,
        "evidence_items",
        (),
    )
    unknown_items = getattr(
        beginner_evidence,
        "unknown_items",
        (),
    )
    limitation_codes = getattr(
        beginner_evidence,
        "limitation_codes",
        (),
    )
    origin_status = _enum_value(
        getattr(beginner_evidence, "origin_status", None)
    )

    evidence = []
    for item in evidence_items:
        channel = _translated_code(
            language,
            getattr(item, "source_channel", None),
            "easy_channel_",
        )
        support = _translated_code(
            language,
            getattr(item, "supports", None),
            "easy_support_",
        )
        entry = {
            "label": f"{channel} ({support})",
            "text": str(getattr(item, "text", "")),
            "is_truncated": bool(
                getattr(item, "is_truncated", False)
            ),
            "is_direct_behavior": not (
                _enum_value(getattr(item, "source_channel", None))
                == "code_diff"
                and _enum_value(getattr(item, "scope", None))
                in {"history_only", "out_of_target"}
            ),
        }
        evidence.append(entry)

    unknown = []
    for code in unknown_items:
        unknown.append(
            translate(
                language,
                {
                    "unrecorded_developer_intent": (
                        "easy_unknown_developer_intent"
                    ),
                    "exact_change_reason_not_recorded": (
                        "easy_unknown_change_reason"
                    ),
                    "truncated_reference_context": (
                        "easy_unknown_truncated_context"
                    ),
                }.get(
                    _enum_value(code),
                    "easy_unknown_information",
                ),
            )
        )

    limitations = [
        translate(
            language,
            {
                "history_partial": "easy_limitation_history_partial",
                "rollback_history": "easy_limitation_rollback_history",
            }.get(
                _enum_value(code),
                "easy_unknown_limitation",
            ),
        )
        for code in limitation_codes
    ]

    reason_key = {
        "explicit_text": "easy_reason_explicit_text",
        "title_only": "easy_reason_title_only",
        "not_recorded": "easy_reason_not_recorded",
        "withheld": "easy_reason_withheld",
    }.get(reason_status, "easy_reason_not_recorded")

    return {
        "available": True,
        "target_question": translate(language, "easy_target_question"),
        "reason_question": translate(language, "easy_reason_question"),
        "evidence_question": translate(language, "easy_evidence_question"),
        "unknown_question": translate(language, "easy_unknown_question"),
        "limitations_question": translate(
            language,
            "easy_limitations_question",
        ),
        "reason_status": translate(language, reason_key),
        "evidence": evidence,
        "unknown_items": unknown,
        "limitations": limitations,
        "origin": (
            translate(language, "easy_origin_observed")
            if origin_status == "observed_in_history"
            else ""
        ),
        "truncated_notice": translate(
            language,
            "easy_truncated_notice",
        ),
    }
