DIRECT = "DIRECT"
PARTIAL = "PARTIAL"
INFERRED = "INFERRED"
NONE = "NONE"
CONFLICTING = "CONFLICTING"

BEHAVIOR = "BEHAVIOR"


def make_behavior_semantics(
    *,
    action=None,
    subject=None,
    condition=None,
    target=None,
    scope=None,
    source_event=None,
):
    """
    BEHAVIOR Claim의 구조화된 의미를 생성합니다.

    이 함수는 의미를 추론하지 않습니다.
    이미 추출된 semantic field를 구조화하기만 합니다.
    """
    return {
        "type": BEHAVIOR,
        "action": action,
        "subject": subject,
        "condition": condition,
        "target": target,
        "scope": scope,
        "source_event": source_event,
        "field_evidence": {},
        "entailment": NONE,
    }


def attach_field_evidence(
    semantics,
    field,
    *,
    source,
    ref,
    level=DIRECT,
):
    """
    Structured semantic field 하나에 Evidence를 연결합니다.

    예:
        condition
        -> DIFF
        -> commit abc123
        -> DIRECT

    입력 semantics 자체는 수정하지 않고 복사본을 반환합니다.
    """
    if field not in {
        "action",
        "subject",
        "condition",
        "target",
        "scope",
    }:
        raise ValueError(
            f"Unsupported semantic field: {field}"
        )

    if level not in {
        DIRECT,
        PARTIAL,
        INFERRED,
        NONE,
        CONFLICTING,
    }:
        raise ValueError(
            f"Unsupported entailment level: {level}"
        )

    result = dict(semantics)

    evidence = {
        key: list(value)
        for key, value in semantics.get(
            "field_evidence",
            {},
        ).items()
    }

    evidence.setdefault(
        field,
        [],
    )

    evidence[field].append(
        {
            "source": source,
            "ref": ref,
            "level": level,
        }
    )

    result["field_evidence"] = evidence

    return result


def get_present_fields(semantics):
    """
    값이 실제로 존재하는 semantic field 이름을 반환합니다.
    """
    fields = []

    for field in (
        "action",
        "subject",
        "condition",
        "target",
        "scope",
    ):
        value = semantics.get(field)

        if value is not None and value != "":
            fields.append(field)

    return fields


def get_field_evidence(
    semantics,
    field,
):
    """
    특정 semantic field에 연결된 Evidence 목록을 반환합니다.
    """
    return list(
        semantics.get(
            "field_evidence",
            {},
        ).get(
            field,
            [],
        )
    )