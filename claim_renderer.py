import re

from claim_evidence import (
    BEHAVIOR,
    SUPPORTED,
)


def _extract_added_code(text):
    """
    Adapter가 생성한 'Added code: ...' 형식에서
    실제 코드 부분만 추출합니다.
    """
    prefix = "Added code: "

    if not isinstance(text, str):
        return ""

    if not text.startswith(prefix):
        return ""

    return text[len(prefix):].strip()


def render_behavior_claim(claim):
    """
    SUPPORTED BEHAVIOR Claim을 Evidence-safe 자연어로 변환합니다.

    v1 원칙:
    - Diff에서 직접 확인 가능한 동작만 표현합니다.
    - 성능, 보안, 사용자 의도와 같은 원인을 추론하지 않습니다.
    - 이해하지 못하는 코드는 원래 Claim을 그대로 유지합니다.
    """
    if claim.get("type") != BEHAVIOR:
        return claim.get("text", "")

    if claim.get("status") != SUPPORTED:
        return claim.get("text", "")

    text = claim.get("text", "")
    code = _extract_added_code(text)

    if not code:
        return text

    utf8_match = re.fullmatch(
        r'([A-Za-z_][A-Za-z0-9_]*)\s*='
        r'\s*\1\.encode\(["\']utf-8["\']\)',
        code,
    )

    if utf8_match:
        variable = utf8_match.group(1)

        return (
            f"{variable} is encoded as UTF-8."
        )

    isinstance_match = re.fullmatch(
        r"if isinstance\("
        r"([A-Za-z_][A-Za-z0-9_]*),"
        r"\s*str\):",
        code,
    )

    if isinstance_match:
        variable = isinstance_match.group(1)

        return (
            f"The code checks whether {variable} "
            f"is a string."
        )

    return text


def render_supported_claims(claims):
    """
    SUPPORTED Claim 리스트를 사용자에게 표시 가능한
    Evidence-safe 문장 리스트로 변환합니다.

    Claim의 Evidence 판정 자체는 변경하지 않습니다.
    """
    rendered = []

    for claim in claims:
        if claim.get("status") != SUPPORTED:
            continue

        if claim.get("type") == BEHAVIOR:
            text = render_behavior_claim(
                claim
            )
        else:
            text = claim.get("text", "")

        if text:
            rendered.append(text)

    return rendered