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

def _extract_call_use(
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

    subject = ast.unparse(
        node.value.func
    )

    if not subject:
        return None

    semantics = make_behavior_semantics(
        action="USE",
        subject=subject,
        source_event=source_event,
    )

    for field in (
        "action",
        "subject",
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

def extract_conditional_assignment_flows(
    source,
    source_event,
):
    """
    Extract directly observable conditional data flows.

    Recognized structure:

        if condition:
            temporary = producer_call()

        consumer(..., field=temporary, ...)

    Safety rules:
    - The producer must be a direct call assigned to one name.
    - The producer condition must be explicit in the AST.
    - The consumer must directly use the temporary as an argument.
    - Exactly one matching consumer use must exist.
    - Every rendered semantic field receives DIRECT DIFF evidence.
    - No causal or intentional meaning is inferred.
    """
    if not isinstance(source, str):
        return []

    if not source.strip():
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    result = []

    def direct_call_from_statement(statement):
        if (
            isinstance(statement, ast.Assign)
            and isinstance(statement.value, ast.Call)
        ):
            return statement.value

        if (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.value, ast.Call)
        ):
            return statement.value

        if (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Call)
        ):
            return statement.value

        return None

    def assignment_target_name(statement):
        if isinstance(statement, ast.Assign):
            if len(statement.targets) != 1:
                return None

            target = statement.targets[0]

            if isinstance(target, ast.Name):
                return target.id

            return None

        if (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
        ):
            return statement.target.id

        return None

    def iter_if_branches(node):
        current = node

        while isinstance(current, ast.If):
            yield current.test, current.body

            if (
                len(current.orelse) == 1
                and isinstance(current.orelse[0], ast.If)
            ):
                current = current.orelse[0]
                continue

            if current.orelse:
                yield None, current.orelse

            break

    def consumer_uses(call, variable):
        uses = []

        for index, argument in enumerate(call.args):
            if (
                isinstance(argument, ast.Name)
                and argument.id == variable
            ):
                uses.append(
                    (
                        f"argument {index + 1}",
                        argument,
                    )
                )

        for keyword in call.keywords:
            if keyword.arg is None:
                continue

            if (
                isinstance(keyword.value, ast.Name)
                and keyword.value.id == variable
            ):
                uses.append(
                    (
                        keyword.arg,
                        keyword.value,
                    )
                )

        return uses

    def consumer_target(call, use_name):
        function_name = ast.unparse(call.func).strip()

        if not function_name:
            return None

        return f"{function_name} {use_name}"

    def inspect_block(statements):
        for index, statement in enumerate(statements):
            if isinstance(statement, ast.If):
                following = statements[index + 1:]

                for condition_node, branch in iter_if_branches(statement):
                    if condition_node is None:
                        continue

                    condition = ast.unparse(
                        condition_node
                    ).strip()

                    if not condition:
                        continue

                    for branch_statement in branch:
                        variable = assignment_target_name(
                            branch_statement
                        )
                        producer_call = direct_call_from_statement(
                            branch_statement
                        )

                        if not variable or producer_call is None:
                            continue

                        producer = ast.unparse(
                            producer_call
                        ).strip()

                        if not producer:
                            continue

                        matches = []

                        for later_statement in following:
                            consumer_call = direct_call_from_statement(
                                later_statement
                            )

                            if consumer_call is None:
                                continue

                            for use_name, _ in consumer_uses(
                                consumer_call,
                                variable,
                            ):
                                target = consumer_target(
                                    consumer_call,
                                    use_name,
                                )

                                if target:
                                    matches.append(target)

                        if len(matches) != 1:
                            continue

                        semantics = make_behavior_semantics(
                            action="USE",
                            subject=producer,
                            condition=condition,
                            target=matches[0],
                            source_event=source_event,
                        )

                        for field in (
                            "action",
                            "subject",
                            "condition",
                            "target",
                        ):
                            semantics = attach_field_evidence(
                                semantics,
                                field,
                                source="DIFF",
                                ref=source_event,
                                level=DIRECT,
                            )

                        result.append(semantics)

            nested_blocks = []

            if isinstance(
                statement,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.For,
                    ast.AsyncFor,
                    ast.While,
                    ast.With,
                    ast.AsyncWith,
                    ast.Try,
                ),
            ):
                nested_blocks.append(statement.body)

            if isinstance(statement, ast.Try):
                nested_blocks.extend(
                    handler.body
                    for handler in statement.handlers
                )
                nested_blocks.append(statement.orelse)
                nested_blocks.append(statement.finalbody)

            for nested in nested_blocks:
                if nested:
                    inspect_block(nested)

    inspect_block(tree.body)
    return result


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

        return_semantics = _extract_return(
            node,
            source_event,
        )

        if return_semantics:
            result.append(
                return_semantics
            )

        if isinstance(node, ast.If):
            condition = ast.unparse(node.test)

            for child in node.body:
                child_semantics = _extract_encode_assignment(
                    child,
                    source_event,
                )

                if not child_semantics:
                    child_semantics = _extract_call_use(
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


def _extract_returned_recursive_python_fallback(
    source_tree,
    direct_helper_names,
    source_event,
):
    function_defs = {
        node.name: node
        for node in source_tree.body
        if isinstance(node, ast.FunctionDef)
    }

    returned_helper_names = set()

    for helper_name in direct_helper_names:
        helper_node = function_defs.get(
            helper_name
        )

        if helper_node is None:
            continue

        for child in ast.walk(helper_node):
            if not isinstance(
                child,
                ast.Return,
            ):
                continue

            if not isinstance(
                child.value,
                ast.Call,
            ):
                continue

            if not isinstance(
                child.value.func,
                ast.Name,
            ):
                continue

            returned_helper_names.add(
                child.value.func.id
            )

    result = []

    for helper_name in sorted(
        returned_helper_names
    ):
        helper_node = function_defs.get(
            helper_name
        )

        if helper_node is None:
            continue

        docstring = (
            ast.get_docstring(helper_node)
            or ""
        )

        if "Pure-Python fallback" not in docstring:
            continue

        is_recursive = any(
            isinstance(child, ast.Call)
            and isinstance(
                child.func,
                ast.Name,
            )
            and child.func.id == helper_name
            for child in ast.walk(helper_node)
        )

        if not is_recursive:
            continue

        semantics = make_behavior_semantics(
            action="USE",
            subject=helper_name,
            target=(
                "Pure-Python recursive fallback"
            ),
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

        result.append(semantics)

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

    result.extend(
        _extract_returned_recursive_python_fallback(
            source_tree,
            helper_names,
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
        if isinstance(
            node,
            (
                ast.ClassDef,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            function_code = ast.unparse(
                ast.Module(
                    body=node.body,
                    type_ignores=[],
                )
            )

            result.extend(
                extract_statement_ordering(
                    function_code,
                    source_event,
                )
            )
            continue

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
