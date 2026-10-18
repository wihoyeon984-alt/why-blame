CONFIDENCE_ORDER = (
    "VERY_HIGH",
    "HIGH",
    "MEDIUM",
    "LOW",
    "WEAK",
    "VERY_WEAK",
    "BLOCKED",
    "UNKNOWN",
)


def format_rate(value):
    if value is None:
        return "N/A"

    return f"{value:.3f}"


def _ordered_levels(metrics):
    known = [
        level
        for level in CONFIDENCE_ORDER
        if level in metrics
    ]

    additional = sorted(
        level
        for level in metrics
        if level not in CONFIDENCE_ORDER
    )

    return known + additional


def print_confidence_metrics(metrics):
    print("Confidence-stratified metrics")
    print("-----------------------------")

    if not metrics:
        print("No confidence data.")
        return

    for index, level in enumerate(
        _ordered_levels(metrics)
    ):
        if index:
            print()

        group = metrics[level]

        print(level)
        print(
            "  Cases:                     "
            f"{group['case_count']}"
        )
        print(
            "  Supported total:           "
            f"{group['supported_total']}"
        )
        print(
            "  Supported presented:       "
            f"{group['supported_presented']}"
        )
        print(
            "  Total presentations:       "
            f"{group['total_presentations']}"
        )
        print(
            "  Unsafe presented:          "
            f"{group['unsafe_presented']}"
        )
        print(
            "  Claim precision:           "
            + format_rate(
                group["claim_precision"]
            )
        )
        print(
            "  Supported recall:          "
            + format_rate(
                group["supported_recall"]
            )
        )
        print(
            "  Unsafe presentation rate:  "
            + format_rate(
                group[
                    "unsafe_presentation_rate"
                ]
            )
        )

def print_withheld_reason_summary(summary):
    print("WITHHELD reason coverage")
    print("------------------------")
    print(
        "Total WITHHELD:        "
        f"{summary['total']}"
    )
    print(
        "Reason specified:      "
        f"{summary['specified']}"
    )
    print(
        "Reason unspecified:    "
        f"{summary['unspecified']}"
    )
    print()
    print("By reason")

    for reason, count in summary["by_reason"].items():
        print(f"  {reason}: {count}")
