import ast

from claim_semantics import (
    DIRECT,
    attach_field_evidence,
    make_behavior_semantics,
)


def _source_name(node):
    """
    AST node에서 보수적으로 source 표현을 추출합니다.

    지원하지 않는 구조는 빈 문자열을 반환합니다.
    """
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent = _source_name(
            node.value
        )

        if parent:
            return (
                f"{parent}.{node.attr}"
            )

        return node.attr

    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return node.value

    return ""


def _extract_encode_assignment(
    node,
    source_event,
):
    """
    다음과 같은 직접적인 encode assignment를 추출합니다.

        o = o.encode("utf-8")

    Structured semantics:

        action  = ENCODE
        subject = o
        target  = UTF-8

    이 함수는 encode 사용 목적을 추론하지 않습니다.
    """
    if not isinstance(
        node,
        ast.Assign,
    ):
        return None

    if len(node.targets) != 1:
        return None

    target_node = node.targets[0]

    if not isinstance(
        target_node,
        ast.Name,
    ):
        return None

    value = node.value

    if not isinstance(
        value,
        ast.Call,
    ):
        return None

    function = value.func

    if not isinstance(
        function,
        ast.Attribute,
    ):
        return None

    if function.attr != "encode":
        return None

    source = _source_name(
        function.value
    )

    assigned = target_node.id

    if not source:
        return None

    if source != assigned:
        return None

    if len(value.args) != 1:
        return None

    encoding = _source_name(
        value.args[0]
    )

    if not encoding:
        return None

    normalized_encoding = (
        encoding.upper()
        if encoding.lower() == "utf-8"
        else encoding
    )

    semantics = make_behavior_semantics(
        action="ENCODE",
        subject=assigned,
        target=normalized_encoding,
        source_event=source_event,
    )

    for field in (
        "action",
        "subject",
        "target",
    ):
        semantics = attach_field_evidence(
            semantics,
            field,
            source="DIFF",
            ref=source_event,
            level=DIRECT,
        )

    return semantics


def extract_statement_semantics(
    code,
    source_event,
):
    """
    Python statement 하나에서 직접 증명 가능한
    Structured Semantics를 추출합니다.

    이해하지 못하는 코드는 빈 리스트를 반환합니다.
    """
    if not isinstance(code, str):
        return []

    code = code.strip()

    if not code:
        return []

    try:
        tree = ast.parse(
            code
        )
    except SyntaxError:
        return []

    result = []

    for node in tree.body:
        encode_semantics = (
            _extract_encode_assignment(
                node,
                source_event,
            )
        )

        if encode_semantics:
            result.append(
                encode_semantics
            )

    return result


def extract_diff_semantics(
    diff_lines,
    source_event,
):
    """
    추가된 Diff line에서 Structured Semantics를 추출합니다.

    v1에서는 '+' line만 대상으로 합니다.
    삭제된 line은 현재 Behavior로 추출하지 않습니다.
    """
    result = []

    for line in diff_lines:
        if not isinstance(
            line,
            str,
        ):
            continue

        if not line.startswith("+ "):
            continue

        code = line[2:].strip()

        if not code:
            continue

        semantics_items = (
            extract_statement_semantics(
                code,
                source_event,
            )
        )

        result.extend(
            semantics_items
        )

    return result


def extract_target_semantics(
    timeline,
):
    """
    Target-aware v1 policy에 따라 Timeline의
    final event에서만 Structured Semantics를 추출합니다.

    Historical Diff는 semantic rendering 후보로 사용하지 않습니다.
    """
    if not timeline:
        return []

    final_event = timeline[-1]

    return extract_diff_semantics(
        final_event.get(
            "diff_lines",
            [],
        ),
        final_event.get(
            "hash",
            "unknown",
        ),
    )       
