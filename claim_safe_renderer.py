from claim_safety import SAFE_TO_RENDER


def _clean_value(value):
    """
    Template에 삽입할 semantic value를 안전하게 정규화합니다.

    새로운 의미를 만들지 않습니다.
    """
    if not isinstance(value, str):
        return ""

    return value.strip()


def render_safe_semantics(semantics):
    """
    SAFE_TO_RENDER 판정을 받은 Structured BEHAVIOR만
    고정 Template으로 자연어화합니다.

    Safety rules:
    - semantic_safety가 SAFE_TO_RENDER가 아니면 렌더링하지 않습니다.
    - 존재하지 않는 field를 추론해서 채우지 않습니다.
    - 지원하지 않는 action은 렌더링하지 않습니다.
    - CAUSE나 의도는 생성하지 않습니다.
    """
    if not isinstance(semantics, dict):
        return None

    if (
        semantics.get("semantic_safety")
        != SAFE_TO_RENDER
    ):
        return None

    action = _clean_value(
        semantics.get("action")
    ).upper()

    subject = _clean_value(
        semantics.get("subject")
    )

    condition = _clean_value(
        semantics.get("condition")
    )

    target = _clean_value(
        semantics.get("target")
    )

    if action == "ENCODE":
        if not subject or not target:
            return None

        sentence = (
            f"{subject} is encoded as {target}"
        )

        if condition:
            sentence += (
                f" when {condition}"
            )

        return sentence + "."

    if action == "USE":
        if not subject:
            return None

        sentence = (
            f"{subject} is used"
        )

        if target:
            sentence += (
                f" for {target}"
            )

        if condition:
            sentence += (
                f" when {condition}"
            )

        return sentence + "."

    if action == "AVOID":
        if not subject:
            return None

        sentence = (
            f"{subject} is not used"
        )

        if target:
            sentence += (
                f" for {target}"
            )

        if condition:
            sentence += (
                f" when {condition}"
            )

        return sentence + "."

    if action == "ENABLE":
        if not subject:
            return None

        sentence = (
            f"{subject} is enabled"
        )

        if condition:
            sentence += (
                f" when {condition}"
            )

        return sentence + "."

    if action == "DISABLE":
        if not subject:
            return None

        sentence = (
            f"{subject} is disabled"
        )

        if condition:
            sentence += (
                f" when {condition}"
            )

        return sentence + "."

    if action == "ADD":
        if not subject:
            return None

        return (
            f"{subject} is added."
        )

    if action == "REMOVE":
        if not subject:
            return None

        return (
            f"{subject} is removed."
        )

    return None


def render_safe_semantics_list(
    semantics_items,
):
    """
    SAFE_TO_RENDER Structured Claim 목록을
    안전한 문장 목록으로 변환합니다.

    렌더링할 수 없는 Claim은 제외합니다.
    """
    rendered = []

    for semantics in semantics_items:
        text = render_safe_semantics(
            semantics
        )

        if text:
            rendered.append(
                text
            )

    return rendered