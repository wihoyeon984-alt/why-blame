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


def _extract_return(
    node,
    source_event,
):
    if not isinstance(node, ast.Return):
        return None

    if node.value is None:
        return None

    target = ast.unparse(node.value)

    if not target:
        return None

    semantics = make_behavior_semantics(
        action="RETURN",
        target=target,
        source_event=source_event,
    )

    for field in (
        "action",
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

def _extract_append_call(
    node,
    source_event,
):
    if not isinstance(
        node,
        ast.Expr,
    ):
        return None

    if not isinstance(
        node.value,
        ast.Call,
    ):
        return None

    call = node.value

    if not isinstance(
        call.func,
        ast.Attribute,
    ):
        return None

    if call.func.attr != "append":
        return None

    if len(call.args) != 1:
        return None

    subject = _source_name(
        call.args[0]
    )

    collection = _source_name(
        call.func.value
    )

    if not subject:
        return None

    if not collection:
        return None

    semantics = make_behavior_semantics(
        action="ADD",
        subject=subject,
        target=collection,
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

def find_direct_local_helpers(source, target_statement):
    if not isinstance(source, str) or not isinstance(target_statement, str):
        return []
    try:
        source_tree = ast.parse(source)
        target_tree = ast.parse(target_statement)
    except SyntaxError:
        return []
    called_names = set()
    for node in ast.walk(target_tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            called_names.add(node.func.id)
    local_helpers = []
    for node in source_tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in called_names:
            local_helpers.append(node.name)
    return sorted(local_helpers)

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

        append_semantics = (
            _extract_append_call(
                node,
                source_event,
            )
        )

        if append_semantics:
            result.append(
                append_semantics
            )

        if isinstance(node, ast.If):
            condition = ast.unparse(node.test)

            for child in node.body:
                child_semantics = _extract_encode_assignment(
                    child,
                    source_event,
                )

                if not child_semantics:
                    child_semantics = _extract_return(
                        child,
                        source_event,
                    )

                if not child_semantics:
                    continue

                child_semantics = dict(child_semantics)
                child_semantics["condition"] = condition
                child_semantics = attach_field_evidence(
                    child_semantics,
                    "condition",
                    source="DIFF",
                    ref=source_event,
                    level=DIRECT,
                )

                result.append(child_semantics)
    return result


def extract_direct_local_helper_semantics(
    source,
    target_statement,
    source_event,
):
    helper_names = find_direct_local_helpers(
        source,
        target_statement,
    )

    if not helper_names:
        return []

    try:
        source_tree = ast.parse(source)
    except SyntaxError:
        return []

    result = []

    for node in source_tree.body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name in helper_names
        ):
            for statement in node.body:
                code = ast.unparse(statement)
                result.extend(
                    extract_statement_semantics(
                        code,
                        source_event,
                    )
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
    source_event = final_event.get(
        "hash",
        "unknown",
    )
    diff_lines = final_event.get(
        "diff_lines",
        [],
    )

    result = extract_diff_semantics(
        diff_lines,
        source_event,
    )

    source = final_event.get(
        "source",
        "",
    )

    if not source:
        return result

    for line in diff_lines:
        if not isinstance(line, str):
            continue

        if not line.startswith("+ "):
            continue

        target_statement = line[2:].strip()

        if not target_statement:
            continue

        result.extend(
            extract_direct_local_helper_semantics(
                source,
                target_statement,
                source_event,
            )
        )

    return result

def _extract_block_operations(
    statements,
):
    operations = []

    for node in statements:
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Call)
        ):
            operations.append(
                ast.unparse(node.value)
            )
            continue

        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
        ):
            operations.append(
                ast.unparse(node.value)
            )

    return operations


def _make_ordering_relations(
    operations,
    source_event,
):
    return [
        {
            "before": before,
            "after": after,
            "source_event": source_event,
            "relation": "DIRECT_ORDER",
        }
        for before, after in zip(
            operations,
            operations[1:],
        )
    ]


def extract_statement_ordering(
    code,
    source_event,
):
    if not isinstance(code, str):
        return []

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    result = _make_ordering_relations(
        _extract_block_operations(
            tree.body
        ),
        source_event,
    )

    for node in tree.body:
        if isinstance(node, ast.For):
            result.extend(
                _make_ordering_relations(
                    _extract_block_operations(
                        node.body
                    ),
                    source_event,
                )
            )
            continue

        if isinstance(node, ast.Try):
            for child in node.body:
                if not isinstance(child, ast.For):
                    continue

                result.extend(
                    _make_ordering_relations(
                        _extract_block_operations(
                            child.body
                        ),
                        source_event,
                    )
                )

    return result


def derive_transitive_ordering(ordering):
    result = list(ordering)

    changed = True

    while changed:
        changed = False
        current = list(result)

        for first in current:
            for second in current:
                if (
                    first.get("source_event")
                    != second.get("source_event")
                ):
                    continue

                if first.get("after") != second.get("before"):
                    continue

                relation = {
                    "before": first.get("before"),
                    "after": second.get("after"),
                    "source_event": first.get("source_event"),
                    "relation": "TRANSITIVE_ORDER",
                }

                if relation in result:
                    continue

                result.append(relation)
                changed = True

    return result

def extract_target_ordering(
    timeline,
):
    if not timeline:
        return []

    final_event = timeline[-1]
    source_event = final_event.get(
        "hash",
        "unknown",
    )
    source = final_event.get(
        "source",
        "",
    )

    if not source:
        return []

    return extract_statement_ordering(
        source,
        source_event,
    )
