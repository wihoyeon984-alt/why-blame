from claim_evidence import (
    BEHAVIOR,
    CAUSE,
    REVERT_FACT,
    make_claim,
    make_evidence,
)


def _clean_diff_text(line):
    """
    Timeline Diff 문자열에서 '+ ' 또는 '- ' 접두사를 제거합니다.
    """
    if not isinstance(line, str):
        return ""

    if line.startswith("+ ") or line.startswith("- "):
        return line[2:].strip()

    return line.strip()


def select_target_behavior_events(timeline):
    """
    현재 target의 형태를 설명하는 데 사용할 Timeline event를 선택합니다.

    Target-aware v1 policy:

    - Timeline 전체의 historical added lines를 현재 동작으로 취급하지 않습니다.
    - 현재 target 형태에 가장 가까운 최종 event만 BEHAVIOR source로 사용합니다.
    - Timeline이 비어 있으면 아무 event도 반환하지 않습니다.

    Historical events는 Timeline 설명과 Evidence에는 계속 남지만,
    현재 target의 BEHAVIOR Claim 생성에는 사용하지 않습니다.
    """
    if not timeline:
        return []

    return [timeline[-1]]


def build_behavior_claims(timeline):
    """
    현재 target을 형성한 최종 Timeline event의 추가 Diff를 기반으로
    BEHAVIOR Claim 후보를 생성합니다.

    Historical event의 추가 코드는 현재 target behavior로 승격하지 않습니다.

    v1에서는 인과관계를 추론하지 않습니다.
    선택된 Diff에서 직접 관찰 가능한 사실만 Claim으로 만듭니다.
    """
    claims = []

    target_events = select_target_behavior_events(
        timeline
    )

    for item in target_events:
        diff_lines = item.get("diff_lines", [])

        for line in diff_lines:
            if not isinstance(line, str):
                continue

            if not line.startswith("+ "):
                continue

            code = _clean_diff_text(line)

            if not code:
                continue

            claim = make_claim(
                text=f"Added code: {code}",
                claim_type=BEHAVIOR,
                evidence=[
                    make_evidence(
                        "DIFF",
                        item.get("hash", "unknown"),
                    )
                ],
            )

            claim["source_event"] = item.get(
                "hash",
                "unknown",
            )
            claim["target_relevant"] = True

            claims.append(claim)

    return claims


def build_reference_claims(timeline):
    """
    Timeline에 연결된 성공한 PR / Issue를
    Evidence relationship Claim 후보로 생성합니다.

    PR이나 Issue가 존재한다는 사실만으로
    새로운 구체적 WHY를 만들어내지 않습니다.

    Reference는 historical Evidence로 사용할 수 있으므로
    Timeline 전체에서 수집합니다.
    """
    claims = []

    for item in timeline:
        for ref in item.get("ref_items", []):
            if ref.get("status") != "SUCCESS":
                continue

            ref_type = ref.get("type")

            if ref_type not in {"PR", "ISSUE"}:
                continue

            number = ref.get("number")
            title = (ref.get("title") or "").strip()

            if not number or not title:
                continue

            claim = make_claim(
                text=f"{ref_type} #{number}: {title}",
                claim_type=CAUSE,
                evidence=[
                    make_evidence(
                        ref_type,
                        f"#{number}",
                    )
                ],
            )

            claim["source_event"] = item.get(
                "hash",
                "unknown",
            )

            claims.append(claim)

    return claims


def build_revert_claims(timeline):
    """
    Timeline에서 실제 Revert 사건을 찾아
    REVERT_FACT Claim을 생성합니다.

    Revert의 존재만 기록하며,
    Revert의 구체적인 원인은 추론하지 않습니다.
    """
    claims = []

    for item in timeline:
        event_type = (
            item.get("type") or ""
        ).upper()

        if "REVERT" not in event_type:
            continue

        commit_hash = item.get(
            "hash",
            "unknown",
        )

        claim = make_claim(
            text="An earlier change was explicitly reverted.",
            claim_type=REVERT_FACT,
            evidence=[
                make_evidence(
                    "REVERT",
                    commit_hash,
                )
            ],
        )

        claim["source_event"] = commit_hash

        claims.append(claim)

    return claims


def build_candidate_claims(timeline):
    """
    Timeline에서 Claim-level Evidence 평가에 사용할
    Candidate Claim을 생성합니다.

    v1 역할 분리:

    - BEHAVIOR:
      현재 target을 형성한 최종 event에서만 생성

    - CAUSE / reference:
      Timeline 전체 Evidence에서 수집
      단, Narrative v1에서는 아직 출력하지 않음

    - REVERT_FACT:
      Timeline 전체에서 명시적인 Revert를 수집
    """
    claims = []

    claims.extend(
        build_behavior_claims(timeline)
    )

    claims.extend(
        build_reference_claims(timeline)
    )

    claims.extend(
        build_revert_claims(timeline)
    )

    return claims