VALID_CONFIDENCE_LEVELS = {
    "VERY_HIGH",
    "HIGH",
    "MEDIUM",
    "LOW",
    "WEAK",
    "VERY_WEAK",
    "BLOCKED",
    "UNKNOWN",
}


def normalize_confidence(value):
    if not isinstance(value, str):
        return "UNKNOWN"

    normalized = (
        value.strip()
        .upper()
        .replace("-", "_")
        .replace(" ", "_")
    )

    if normalized not in VALID_CONFIDENCE_LEVELS:
        return "UNKNOWN"

    return normalized
