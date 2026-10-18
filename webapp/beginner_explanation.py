from webapp.i18n import translate


def _enum_value(value):
    return getattr(value, "value", value)


def _translated_code(language, code, prefix):
    key = prefix + _enum_value(code)
    try:
        return translate(language, key)
    except KeyError:
        return translate(language, "easy_unknown_information")


def _behavior_status_text(language, status):
    key = {
        "DIRECTLY_OBSERVED": "easy_behavior_status_direct",
        "PARTIALLY_OBSERVED": "easy_behavior_status_partial",
        "NOT_ESTABLISHED": "easy_behavior_status_not_established",
        "WITHHELD": "easy_behavior_status_withheld",
    }.get(status, "easy_behavior_status_not_established")
    return translate(language, key)


def _behavior_unknown(language, code):
    key = {
        "code_outside_observed_range_not_guaranteed": (
            "easy_behavior_unknown_outside_range"
        ),
    }.get(code, "easy_behavior_unknown_information")
    return translate(language, key)


def _behavior_limitation(language, code):
    key = {
        "behavior_evidence_withheld": (
            "easy_behavior_limitation_withheld"
        ),
        "behavior_not_fully_established": (
            "easy_behavior_limitation_partial"
        ),
        "behavior_not_established": (
            "easy_behavior_limitation_not_established"
        ),
    }.get(code, "easy_behavior_limitation_unknown")
    return translate(language, key)


def _target_label(language, target):
    if not isinstance(target, dict):
        return translate(language, "easy_target_unavailable")

    file_name = target.get("file")
    start_line = target.get("start_line")
    end_line = target.get("end_line")
    valid_line = (
        isinstance(start_line, int)
        and not isinstance(start_line, bool)
        and start_line >= 1
        and isinstance(end_line, int)
        and not isinstance(end_line, bool)
        and end_line >= start_line
    )
    if not isinstance(file_name, str) or not file_name or not valid_line:
        return translate(language, "easy_target_unavailable")

    if start_line == end_line:
        if language == "ko":
            return f"{file_name} · {start_line}번째 줄"
        return f"{file_name} · line {start_line}"

    if language == "ko":
        return f"{file_name} · {start_line}~{end_line}번째 줄"
    return f"{file_name} · lines {start_line}-{end_line}"


def _build_behavior_sections(beginner_behavior, language):
    if not isinstance(beginner_behavior, dict):
        return {
            "behavior_available": False,
            "behavior_fallback": translate(
                language,
                "easy_behavior_fallback",
            ),
            "behavior_status": "",
            "behavior_steps": [],
            "behavior_unknown_items": [],
            "behavior_limitations": [],
        }

    status = beginner_behavior.get("status")
    status_value = _enum_value(status)
    steps = []
    if status_value != "WITHHELD":
        for step in beginner_behavior.get("steps", []):
            if not isinstance(step, dict):
                continue

            is_direct = bool(step.get("is_directly_observed"))
            observation_key = (
                "easy_behavior_observation_direct"
                if is_direct
                else "easy_behavior_observation_partial"
            )
            steps.append(
                {
                    "statement": str(step.get("statement", "")),
                    "code_excerpt": str(
                        step.get("code_excerpt", "")
                    ),
                    "observation_label": translate(
                        language,
                        observation_key,
                    ),
                    "limitations": [
                        _behavior_limitation(language, code)
                        for code in step.get("limitation_codes", [])
                    ],
                }
            )

    return {
        "behavior_available": True,
        "behavior_fallback": "",
        "behavior_status": _behavior_status_text(
            language,
            status_value,
        ),
        "behavior_steps": steps,
        "behavior_unknown_items": [
            _behavior_unknown(language, code)
            for code in beginner_behavior.get(
                "unknown_items",
                [],
            )
        ],
        "behavior_limitations": [
            _behavior_limitation(language, code)
            for code in beginner_behavior.get(
                "limitation_codes",
                [],
            )
        ],
    }


def build_easy_explanation_sections(
    beginner_evidence,
    beginner_behavior=None,
    language="en",
    target=None,
):
    """Build safe, localized display data from stored contracts only."""
    if isinstance(beginner_behavior, str) and language == "en":
        language = beginner_behavior
        beginner_behavior = None

    behavior_sections = _build_behavior_sections(
        beginner_behavior,
        language,
    )

    if beginner_evidence is None and not behavior_sections[
        "behavior_available"
    ]:
        return {
            "available": False,
            "fallback": translate(language, "easy_explanation_fallback"),
            "target_label": _target_label(language, target),
            **behavior_sections,
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

    behavior_limitations = behavior_sections["behavior_limitations"]
    if (
        isinstance(beginner_behavior, dict)
        and _enum_value(beginner_behavior.get("status"))
        == "NOT_ESTABLISHED"
    ):
        behavior_limitations = []

    result = {
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
        "target_label": _target_label(language, target),
    }
    result.update(behavior_sections)
    result["behavior_limitations"] = behavior_limitations
    return result
