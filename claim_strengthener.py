import re


STRENGTHENABLE = "STRENGTHENABLE"
KEEP_RAW = "KEEP_RAW"


_STOP_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "if",
    "in",
    "is",
    "it",
    "not",
    "of",
    "on",
    "or",
    "the",
    "this",
    "to",
    "use",
    "with",
}


def _split_identifier(token):
    """
    snake_case와 CamelCase identifier를 일반적인 단어로 분해합니다.

    예:
        has_poolmanager_ssl_context
        -> has, poolmanager, ssl, context

        SSLContext
        -> ssl, context
    """
    if not isinstance(token, str):
        return []

    parts = []

    for snake_part in token.split("_"):
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
        if part
    ]


def _tokens(text):
    """
    Evidence agreement 비교용 보수적인 token set을 만듭니다.

    일반 Python identifier와 CamelCase 이름은 구성 단어로
    분해해서 비교합니다.
    """
    if not isinstance(text, str):
        return set()

    raw_words = re.findall(
        r"[A-Za-z_][A-Za-z0-9_]*",
        text,
    )

    words = []

    for raw_word in raw_words:
        words.extend(
            _split_identifier(raw_word)
        )

    return {
        word
        for word in words
        if word not in _STOP_WORDS
        and len(word) > 2
    }
def _event_evidence_text(event):
    """
    Target event의 Commit / PR / Issue에서
    검증된 text만 수집합니다.
    """
    parts = []

    message = (
        event.get("message")
        or ""
    ).strip()

    if message:
        parts.append(message)

    for ref in event.get("ref_items", []):
        if ref.get("status") != "SUCCESS":
            continue

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

def _behavior_text(claim):
    """
    Adapter가 생성한 BEHAVIOR Claim에서
    비교 가능한 text를 반환합니다.
    """
    text = (
        claim.get("text")
        or ""
    ).strip()

    prefix = "Added code: "

    if text.startswith(prefix):
        return text[len(prefix):].strip()

    return text

def evaluate_strengthening(claim, timeline):
    """
    하나의 BEHAVIOR Claim을 더 의미 있는 설명으로 강화할
    Evidence가 충분한지 판정합니다.

    v1 Safety Policy:

    - target_relevant Claim만 평가
    - Claim의 source_event와 Timeline final event가 같아야 함
    - final event에 Commit / PR / Issue text Evidence가 있어야 함
    - Behavior와 Evidence 사이에 최소한의 token agreement가 있어야 함

    여기서는 새로운 WHY 문장을 만들지 않습니다.
    강화 가능 여부만 판정합니다.
    """
    if claim.get("type") != "BEHAVIOR":
        return KEEP_RAW

    if claim.get("target_relevant") is not True:
        return KEEP_RAW

    if not timeline:
        return KEEP_RAW

    final_event = timeline[-1]

    source_event = claim.get(
        "source_event"
    )

    final_hash = final_event.get(
        "hash"
    )

    if not source_event or source_event != final_hash:
        return KEEP_RAW

    evidence_text = _event_evidence_text(
        final_event
    )

    if not evidence_text:
        return KEEP_RAW

    behavior_tokens = _tokens(
        _behavior_text(claim)
    )

    evidence_tokens = _tokens(
        evidence_text
    )

    if not behavior_tokens or not evidence_tokens:
        return KEEP_RAW

    overlap = (
        behavior_tokens
        & evidence_tokens
    )

    if overlap:
        return STRENGTHENABLE

    return KEEP_RAW

def collect_strengthenable_claims(claims, timeline):
    """
    Strengthening에 사용할 수 있는 BEHAVIOR Claim만 반환합니다.
    """
    result = []

    for claim in claims:
        if evaluate_strengthening(
            claim,
            timeline,
        ) != STRENGTHENABLE:
            continue

        item = dict(claim)
        item["strengthening"] = STRENGTHENABLE

        result.append(item)

    return result