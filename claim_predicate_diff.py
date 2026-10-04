from claim_predicate import (
    PREDICATE_AND,
    PREDICATE_OR,
)


DELTA_KNOWN = "KNOWN"
DELTA_UNKNOWN = "UNKNOWN"


def _predicate_key(predicate):
    """
    Structured Predicate를 비교 가능한 immutable key로 변환합니다.

    의미를 추론하지 않고 구조적 동일성만 비교합니다.
    """
    if not isinstance(predicate, dict):
        return None

    operation = predicate.get("op")

    if not operation:
        return None

    if "name" in predicate:
        return (
            operation,
            predicate.get("name"),
        )

    if "operand" in predicate:
        operand_key = _predicate_key(
            predicate.get("operand")
        )

        if operand_key is None:
            return None

        return (
            operation,
            operand_key,
        )

    if "values" in predicate:
        value_keys = []

        for value in predicate.get(
            "values",
            [],
        ):
            key = _predicate_key(value)

            if key is None:
                return None

            value_keys.append(key)

        return (
            operation,
            tuple(value_keys),
        )

    return (
        operation,
    )


def _top_level_terms(predicate):
    """
    AND / OR predicate의 직접적인 구성요소를 반환합니다.

    단순 predicate는 자기 자신 하나를 term으로 취급합니다.

    v1에서는 논리식의 대수적 동치나 재배열을 추론하지 않습니다.
    """
    if not isinstance(predicate, dict):
        return None

    operation = predicate.get("op")

    if operation in {
        PREDICATE_AND,
        PREDICATE_OR,
    }:
        values = predicate.get(
            "values"
        )

        if not isinstance(values, list):
            return None

        if not values:
            return None

        return list(values)

    if _predicate_key(predicate) is None:
        return None

    return [predicate]


def compare_predicates(
    old_predicate,
    new_predicate,
):
    """
    old/new Structured Predicate 사이의 구조적 Delta를 계산합니다.

    반환:
    {
        "status": KNOWN | UNKNOWN,
        "preserved": [...],
        "added": [...],
        "removed": [...],
    }

    Safety rules:
    - 두 predicate 모두 구조적으로 이해할 수 있어야 합니다.
    - 구조적 동일성만 비교합니다.
    - identifier 의미는 추론하지 않습니다.
    - boolean algebra simplification은 하지 않습니다.
    """
    old_terms = _top_level_terms(
        old_predicate
    )

    new_terms = _top_level_terms(
        new_predicate
    )

    if old_terms is None or new_terms is None:
        return {
            "status": DELTA_UNKNOWN,
            "preserved": [],
            "added": [],
            "removed": [],
        }

    old_by_key = {}

    for term in old_terms:
        key = _predicate_key(
            term
        )

        if key is None:
            return {
                "status": DELTA_UNKNOWN,
                "preserved": [],
                "added": [],
                "removed": [],
            }

        old_by_key[key] = term

    new_by_key = {}

    for term in new_terms:
        key = _predicate_key(
            term
        )

        if key is None:
            return {
                "status": DELTA_UNKNOWN,
                "preserved": [],
                "added": [],
                "removed": [],
            }

        new_by_key[key] = term

    preserved = [
        new_by_key[key]
        for key in new_by_key
        if key in old_by_key
    ]

    added = [
        new_by_key[key]
        for key in new_by_key
        if key not in old_by_key
    ]

    removed = [
        old_by_key[key]
        for key in old_by_key
        if key not in new_by_key
    ]

    return {
        "status": DELTA_KNOWN,
        "preserved": preserved,
        "added": added,
        "removed": removed,
    }


def predicate_delta_from_code(
    old_code,
    new_code,
):
    """
    old/new if 또는 elif 코드에서
    Structured Predicate Delta를 계산합니다.

    한쪽이라도 Predicate로 추출할 수 없으면
    UNKNOWN을 반환합니다.

    identifier의 의미나 변경 이유는 추론하지 않습니다.
    """
    from claim_predicate import (
        extract_condition_predicate,
    )

    old_predicate = extract_condition_predicate(
        old_code
    )

    new_predicate = extract_condition_predicate(
        new_code
    )

    if (
        old_predicate is None
        or new_predicate is None
    ):
        return {
            "status": DELTA_UNKNOWN,
            "preserved": [],
            "added": [],
            "removed": [],
        }

    return compare_predicates(
        old_predicate,
        new_predicate,
    )