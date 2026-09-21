import re

from claim_predicate import (
    collect_predicate_names,
)
from claim_predicate_diff import (
    DELTA_KNOWN,
)


CHANNEL_COMMIT = "COMMIT"
CHANNEL_PR = "PR"
CHANNEL_ISSUE = "ISSUE"

CANDIDATE = "CANDIDATE"


def _split_identifier(value):
    """
    snake_case와 CamelCase identifier를 일반 token으로 분해합니다.

    이 함수는 의미를 추론하지 않습니다.
    """
    if not isinstance(value, str):
        return []

    parts = []

    for snake_part in value.split("_"):
        if not snake_part:
            continue

        camel_parts = re.findall(
            r"[A-Z]+(?=[A-Z][a-z]|\b)"
            r"|[A-Z]?[a-z]+"
            r"|[A-Z]+"
            r"|[0-9]+",
            snake_part,
        )

        if camel_parts:
            parts.extend(camel_parts)
        else:
            parts.append(snake_part)

    return [
        part.lower()
        for part in parts
        if len(part) > 2
    ]


def _text_tokens(text):
    """
    Evidence text에서 비교용 token을 추출합니다.

    token match는 candidate discovery 용도일 뿐
    entailment proof로 사용하지 않습니다.
    """
    if not isinstance(text, str):
        return set()

    raw_words = re.findall(
        r"[A-Za-z_][A-Za-z0-9_]*",
        text,
    )

    tokens = set()

    for word in raw_words:
        tokens.update(
            _split_identifier(word)
        )

    return tokens


def _predicate_tokens(predicate):
    """
    Structured Predicate에 직접 등장하는 identifier를
    token set으로 변환합니다.
    """
    names = collect_predicate_names(
        predicate
    )

    tokens = set()

    for name in names:
        tokens.update(
            _split_identifier(name)
        )

    return tokens


def _successful_reference_text(ref):
    """
    성공적으로 확인된 PR / Issue의 title과 context만 수집합니다.
    """
    if ref.get("status") != "SUCCESS":
        return ""

    parts = []

    title = (
        ref.get("title")
        or ""
    ).strip()

    body = (
        ref.get("body")
        or ref.get("context")
        or ""
    ).strip()

    if title:
        parts.append(title)

    if body:
        parts.append(body)

    return " ".join(parts)


def collect_event_evidence(event):
    """
    하나의 Timeline event에서 Evidence channel을 수집합니다.

    Commit과 성공한 PR / Issue만 반환합니다.
    """
    result = []

    event_hash = event.get(
        "hash",
        "unknown",
    )

    message = (
        event.get("message")
        or ""
    ).strip()

    if message:
        result.append(
            {
                "channel": CHANNEL_COMMIT,
                "ref": event_hash,
                "text": message,
                "source_event": event_hash,
            }
        )

    for ref in event.get(
        "ref_items",
        [],
    ):
        text = _successful_reference_text(
            ref
        )

        if not text:
            continue

        ref_type = ref.get("type")

        if ref_type == "PR":
            channel = CHANNEL_PR
        elif ref_type == "ISSUE":
            channel = CHANNEL_ISSUE
        else:
            continue

        number = ref.get("number")

        result.append(
            {
                "channel": channel,
                "ref": (
                    f"#{number}"
                    if number
                    else ""
                ),
                "text": text,
                "source_event": event_hash,
            }
        )

    return result


def map_predicate_to_evidence(
    predicate,
    evidence,
):
    """
    Predicate와 Evidence text 사이의 identifier/token overlap을
    이용해 Evidence Candidate를 생성합니다.

    중요:
    이 함수는 DIRECT / PARTIAL / INFERRED를 판정하지 않습니다.
    단지 관련 가능성이 있는 Evidence를 찾습니다.
    """
    predicate_tokens = _predicate_tokens(
        predicate
    )

    evidence_tokens = _text_tokens(
        evidence.get("text")
    )

    overlap = sorted(
        predicate_tokens
        & evidence_tokens
    )

    if not overlap:
        return None

    return {
        "status": CANDIDATE,
        "predicate": predicate,
        "channel": evidence.get(
            "channel"
        ),
        "ref": evidence.get(
            "ref"
        ),
        "source_event": evidence.get(
            "source_event"
        ),
        "matched_tokens": overlap,
        "text": evidence.get(
            "text",
            "",
        ),
    }


def map_delta_to_event_evidence(
    delta,
    event,
):
    """
    Predicate Delta의 added/removed predicate를
    같은 event의 Evidence Candidate와 연결합니다.

    preserved predicate는 현재 v1 mapping 대상에서 제외합니다.

    반환:
    {
        "added": [...],
        "removed": [...]
    }
    """
    result = {
        "added": [],
        "removed": [],
    }

    if delta.get("status") != DELTA_KNOWN:
        return result

    event_evidence = collect_event_evidence(
        event
    )

    for direction in (
        "added",
        "removed",
    ):
        for predicate in delta.get(
            direction,
            [],
        ):
            for evidence in event_evidence:
                candidate = (
                    map_predicate_to_evidence(
                        predicate,
                        evidence,
                    )
                )

                if candidate is None:
                    continue

                item = dict(
                    candidate
                )
                item["direction"] = direction

                result[direction].append(
                    item
                )

    return result