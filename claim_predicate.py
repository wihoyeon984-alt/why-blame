import ast


PREDICATE_NAME = "NAME"
PREDICATE_AND = "AND"
PREDICATE_OR = "OR"
PREDICATE_NOT = "NOT"
PREDICATE_IS_TRUE = "IS_TRUE"
PREDICATE_IS_FALSE = "IS_FALSE"


def _name(node):
    """
    직접 확인 가능한 identifier 이름만 반환합니다.

    복잡하거나 지원하지 않는 표현은 빈 문자열을 반환합니다.
    """
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent = _name(
            node.value
        )

        if parent:
            return (
                f"{parent}.{node.attr}"
            )

        return node.attr

    return ""


def extract_predicate(node):
    """
    Python AST expression에서 직접 확인 가능한
    Boolean Predicate 구조를 추출합니다.

    지원하는 구조:
    - identifier
    - not expression
    - and
    - or
    - value is True
    - value is False

    지원하지 않는 표현은 None을 반환합니다.

    이 함수는 identifier의 의미를 추론하지 않습니다.
    """
    if isinstance(node, ast.Name):
        return {
            "op": PREDICATE_NAME,
            "name": node.id,
        }

    if isinstance(node, ast.Attribute):
        value = _name(
            node
        )

        if not value:
            return None

        return {
            "op": PREDICATE_NAME,
            "name": value,
        }

    if isinstance(node, ast.UnaryOp):
        if not isinstance(
            node.op,
            ast.Not,
        ):
            return None

        operand = extract_predicate(
            node.operand
        )

        if operand is None:
            return None

        return {
            "op": PREDICATE_NOT,
            "operand": operand,
        }

    if isinstance(node, ast.BoolOp):
        if isinstance(
            node.op,
            ast.And,
        ):
            operation = PREDICATE_AND

        elif isinstance(
            node.op,
            ast.Or,
        ):
            operation = PREDICATE_OR

        else:
            return None

        values = []

        for value in node.values:
            predicate = extract_predicate(
                value
            )

            if predicate is None:
                return None

            values.append(
                predicate
            )

        if not values:
            return None

        return {
            "op": operation,
            "values": values,
        }

    if isinstance(node, ast.Compare):
        if (
            len(node.ops) != 1
            or len(node.comparators) != 1
        ):
            return None

        if not isinstance(
            node.ops[0],
            ast.Is,
        ):
            return None

        left_name = _name(
            node.left
        )

        if not left_name:
            return None

        comparator = node.comparators[0]

        if not isinstance(
            comparator,
            ast.Constant,
        ):
            return None

        if comparator.value is True:
            return {
                "op": PREDICATE_IS_TRUE,
                "name": left_name,
            }

        if comparator.value is False:
            return {
                "op": PREDICATE_IS_FALSE,
                "name": left_name,
            }

        return None

    return None


def extract_condition_predicate(
    code,
):
    """
    if / elif 형태의 Python condition에서
    Structured Predicate를 추출합니다.

    단일 Diff line처럼 body가 없는 조건문도 처리하기 위해
    임시 pass body를 붙여 AST로 parsing합니다.

    의미를 해석하지 않고 문법 구조만 반환합니다.
    """
    if not isinstance(
        code,
        str,
    ):
        return None

    code = code.strip()

    if not code:
        return None

    if code.startswith("elif "):
        code = (
            "if "
            + code[len("elif "):]
        )

    if not code.startswith("if "):
        return None

    if not code.endswith(":"):
        return None

    source = (
        code
        + "\n"
        + "    pass"
    )

    try:
        tree = ast.parse(
            source
        )
    except SyntaxError:
        return None

    if len(tree.body) != 1:
        return None

    statement = tree.body[0]

    if not isinstance(
        statement,
        ast.If,
    ):
        return None

    return extract_predicate(
        statement.test
    )


def collect_predicate_names(
    predicate,
):
    """
    Structured Predicate에 직접 등장하는 identifier를
    순서대로 수집합니다.

    의미나 별칭은 추론하지 않습니다.
    """
    if not isinstance(
        predicate,
        dict,
    ):
        return []

    operation = predicate.get(
        "op"
    )

    if operation in {
        PREDICATE_NAME,
        PREDICATE_IS_TRUE,
        PREDICATE_IS_FALSE,
    }:
        name = predicate.get(
            "name"
        )

        if name:
            return [name]

        return []

    if operation == PREDICATE_NOT:
        return collect_predicate_names(
            predicate.get(
                "operand"
            )
        )

    if operation in {
        PREDICATE_AND,
        PREDICATE_OR,
    }:
        result = []

        for value in predicate.get(
            "values",
            [],
        ):
            result.extend(
                collect_predicate_names(
                    value
                )
            )

        return result

    return []