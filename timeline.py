from dataclasses import dataclass, field
from typing import List, Tuple

from consistency import check_evidence_consistency


@dataclass
class ConfidenceReport:
    """Confidence Model v2 평가 결과 데이터 클래스."""

    availability: str
    # HIGH, MODERATE, LOW

    consistency: str
    # HIGH, MODERATE, INCONSISTENT, UNLINKED

    source_reliability: str
    # HIGH, MODERATE, LOW

    history_ambiguity: str
    # LOW, MEDIUM, HIGH

    overall_confidence: str
    # VERY HIGH, HIGH, MEDIUM, MODERATE, LOW, WEAK

    is_blocked: bool = False
    has_rollback: bool = False

    rollback_commits: List[str] = field(
        default_factory=list
    )

    limitations: List[str] = field(
        default_factory=list
    )


def classify_commit(
    message: str,
    is_revert: bool = False,
) -> str:
    """
    Commit message를 바탕으로 변경 유형을 분류한다.

    Revert는 단순히 message 내부에 단어가 존재하는지만
    확인하지 않고, 실제 Revert 여부 또는 message 시작 부분을
    기준으로 우선 판정한다.
    """
    m_low = message.strip().lower()

    if is_revert or m_low.startswith("revert"):
        return "🔄 REVERT"

    prefix = (
        m_low.split(":")[0].strip()
        if ":" in m_low
        else ""
    )

    if prefix in ["feat", "feature"]:
        return "✨ FEATURE"

    if prefix in ["fix", "bug", "hotfix", "patch"]:
        return "🐛 BUG FIX"

    if prefix in ["revert", "rollback"]:
        return "🔄 REVERT"

    if prefix in ["refactor", "cleanup"]:
        return "♻️ REFACTOR"

    if prefix in ["test", "tests"]:
        return "🧪 TEST"

    if prefix in ["docs"]:
        return "📝 DOCS"

    if prefix in ["perf"]:
        return "⚡ PERF"

    if prefix in ["sec", "security"]:
        return "🔒 SECURITY"

    # Conventional Commit 형식이 아닌 경우 keyword fallback
    if any(
        keyword in m_low
        for keyword in [
            "fix",
            "bug",
            "patch",
            "resolve",
            "prevent",
        ]
    ):
        return "🐛 BUG FIX"

    if any(
        keyword in m_low
        for keyword in [
            "feat",
            "add",
            "implement",
        ]
    ):
        return "✨ FEATURE"

    if any(
        keyword in m_low
        for keyword in [
            "refactor",
            "cleanup",
        ]
    ):
        return "♻️ REFACTOR"

    return "📦 UPDATE"


def calculate_availability(
    has_message: bool,
    has_diff: bool,
    has_refs: bool,
    has_context: bool,
) -> str:
    """
    Evidence Availability를 평가한다.

    HIGH:
        Commit message + Diff + Reference + Context

    MODERATE:
        Commit message와 Diff 또는 Reference 존재

    LOW:
        그보다 적은 Evidence만 존재
    """
    if (
        has_message
        and has_diff
        and has_refs
        and has_context
    ):
        return "HIGH"

    if has_message and (has_diff or has_refs):
        return "MODERATE"

    return "LOW"


def calculate_consistency(
    timeline: list,
    has_refs: bool,
) -> Tuple[str, List[str]]:
    """
    Commit과 연결된 PR Evidence 사이의 맥락 일관성을 평가한다.

    반환:
        consistency level
        inconsistent pair descriptions
    """
    has_inconsistent = False
    has_consistent = False

    inconsistent_pairs = []

    for item in timeline:
        commit_message = item.get(
            "message",
            "",
        )

        for ref in item.get("ref_items", []):
            if (
                ref.get("title")
                and ref.get("type") == "PR"
            ):
                check = check_evidence_consistency(
                    commit_message,
                    ref.get("title", ""),
                    ref.get("body_summary", ""),
                )

                if check.get("level") == "INCONSISTENT":
                    has_inconsistent = True

                    inconsistent_pairs.append(
                        f"Commit '{commit_message[:25]}' "
                        f"<-> PR #{ref.get('number')} "
                        f"'{ref.get('title', '')[:25]}'"
                    )

                elif check.get("level") == "HIGH":
                    has_consistent = True

    if has_inconsistent:
        return (
            "INCONSISTENT",
            inconsistent_pairs,
        )

    if has_consistent:
        return "HIGH", []

    if not has_refs:
        return "UNLINKED", []

    return "MODERATE", []


def calculate_source_reliability(
    timeline: list,
    has_refs: bool,
) -> str:
    """
    외부 Evidence Source의 신뢰도를 평가한다.
    """
    if not has_refs:
        return "LOW"

    has_verified_api = any(
        any(
            ref.get("status") == "SUCCESS"
            and ref.get("title")
            for ref in item.get(
                "ref_items",
                [],
            )
        )
        for item in timeline
    )

    if has_verified_api:
        return "HIGH"

    return "MODERATE"


def calculate_history_ambiguity(
    timeline: list,
    reverts_count: int,
) -> Tuple[str, bool, List[str]]:
    """
    변경 이력의 모호성을 평가한다.

    Revert/Rollback이 존재하면 History Ambiguity를 HIGH로
    판단하고 해당 Commit message를 보존한다.
    """
    rollback_commits = [
        item.get("message", "")
        for item in timeline
        if (
            item.get("is_revert")
            or item.get(
                "message",
                "",
            )
            .strip()
            .lower()
            .startswith("revert")
        )
    ]

    if (
        reverts_count > 0
        or len(rollback_commits) > 0
    ):
        return (
            "HIGH",
            True,
            rollback_commits,
        )

    if len(timeline) >= 3:
        return "MEDIUM", False, []

    return "LOW", False, []


def decide_overall_confidence(
    availability: str,
    consistency: str,
    source_reliability: str,
    history_ambiguity: str,
) -> Tuple[str, bool, List[str]]:
    """
    Confidence Model v2 결정 Matrix.

    정책:
    1. INCONSISTENT
       -> LOW + WHY BLOCKED

    2. UNLINKED
       -> WEAK

    3. HIGH consistency + LOW availability
       -> MODERATE

    4. HIGH consistency + MODERATE/HIGH availability
       -> HIGH 또는 VERY HIGH

    5. Revert detected
       -> History Ambiguity HIGH
       -> Confidence 상한 MEDIUM

    중요한 원칙:
    Confidence가 높더라도 Evidence 밖의 WHY를
    생성할 수 있는 권한이 생기는 것은 아니다.
    """
    limitations = []
    is_blocked = False

    if consistency == "INCONSISTENT":
        overall = "LOW (증거 불일치)"
        is_blocked = True

        limitations.append(
            "Evidence 간 맥락 불일치가 확인되어 "
            "신뢰도가 낮아졌으며 WHY 생성을 차단합니다."
        )

    elif consistency == "UNLINKED":
        overall = "WEAK"

        limitations.append(
            "연결된 PR/Issue Evidence가 확인되지 않아 "
            "코드 변경 이유에 대한 신뢰도가 제한적입니다."
        )

    elif consistency == "HIGH":
        if availability == "LOW":
            overall = "MODERATE"

            limitations.append(
                "Evidence의 맥락은 일치하지만 "
                "사용 가능한 Evidence의 양이 제한적입니다."
            )

        elif availability == "MODERATE":
            overall = "HIGH"

        else:
            # HIGH availability
            if source_reliability == "HIGH":
                overall = "VERY HIGH"
            else:
                overall = "HIGH"

    else:
        # MODERATE consistency
        if availability == "HIGH":
            overall = "HIGH"

        elif availability == "MODERATE":
            overall = "MODERATE"

        else:
            overall = "WEAK"

    # ---------------------------------------------------------
    # Revert / History Ambiguity Confidence Cap
    # ---------------------------------------------------------
    if history_ambiguity == "HIGH":
        limitations.append(
            "Rollback history increases ambiguity."
        )

        if overall in [
            "VERY HIGH",
            "HIGH",
        ]:
            overall = "MEDIUM"

    return (
        overall,
        is_blocked,
        limitations,
    )


def calculate_evidence_strength(
    timeline: list,
) -> dict:
    """
    Confidence Model v2 통합 계산 함수.

    기존 Evidence Score와 Confidence Model v2의 결과를
    함께 계산하여 Viewer와 Narrative에 전달한다.
    """
    total = len(timeline)

    reverts = sum(
        1
        for item in timeline
        if item.get("is_revert")
    )

    has_diff = any(
        len(
            item.get(
                "diff_lines",
                [],
            )
        ) > 0
        for item in timeline
    )

    # ---------------------------------------------------------
    # 유효한 Reference 확인
    # ---------------------------------------------------------
    #
    # NOT_FOUND는 Evidence로 인정하지 않는다.
    #
    valid_refs_exist = False

    for item in timeline:
        if item.get("ref_items"):
            if any(
                (
                    ref.get("status") == "SUCCESS"
                    or (
                        ref.get("title")
                        and ref.get("status")
                        != "NOT_FOUND"
                    )
                )
                for ref in item.get(
                    "ref_items",
                    [],
                )
            ):
                valid_refs_exist = True

        elif item.get("refs"):
            valid_refs_exist = True

    has_refs = valid_refs_exist

    has_fetched = any(
        any(
            ref.get("title")
            for ref in item.get(
                "ref_items",
                [],
            )
        )
        or any(
            "'" in detail
            for detail in item.get(
                "ref_details",
                [],
            )
        )
        for item in timeline
    )

    has_context = any(
        any(
            ref.get("body_summary")
            for ref in item.get(
                "ref_items",
                [],
            )
        )
        for item in timeline
    )

    has_message = (
        total > 0
        and any(
            len(
                item.get(
                    "message",
                    "",
                )
            ) > 5
            for item in timeline
        )
    )

    # ---------------------------------------------------------
    # 1. Confidence Model v2의 4개 차원 평가
    # ---------------------------------------------------------
    availability = calculate_availability(
        has_message,
        has_diff,
        has_refs,
        has_context,
    )

    consistency, inconsistent_pairs = (
        calculate_consistency(
            timeline,
            has_refs,
        )
    )

    source_reliability = (
        calculate_source_reliability(
            timeline,
            has_refs,
        )
    )

    (
        history_ambiguity,
        has_rollback,
        rollback_commits,
    ) = calculate_history_ambiguity(
        timeline,
        reverts,
    )

    # ---------------------------------------------------------
    # 2. 최종 Confidence 계산
    # ---------------------------------------------------------
    (
        overall_confidence,
        is_blocked,
        limitations,
    ) = decide_overall_confidence(
        availability,
        consistency,
        source_reliability,
        history_ambiguity,
    )

    # ---------------------------------------------------------
    # 3. 기존 Evidence Score 호환 계산
    # ---------------------------------------------------------
    score = 0

    if has_message:
        score += 2

    if has_diff:
        score += 2

    if has_refs:
        score += 3

    if has_fetched:
        score += 2

    if has_context:
        score += 3

    score = min(
        12,
        score,
    )

    if score >= 11:
        grade = "VERY HIGH"

    elif score >= 8:
        grade = "HIGH"

    elif score >= 5:
        grade = "MODERATE"

    elif score >= 3:
        grade = "WEAK"

    else:
        grade = "LOW"

    if has_rollback:
        ambiguity_desc = (
            f"COMPLEX ({reverts}회 롤백 이력)"
        )

    elif history_ambiguity == "MEDIUM":
        ambiguity_desc = (
            "MODERATE (다단계 변경 이력)"
        )

    else:
        ambiguity_desc = (
            "LOW (단순 변경 이력)"
        )

    coverage_pct = (
        f"{int(score / 12 * 100)}%"
    )

    report = ConfidenceReport(
        availability=availability,
        consistency=consistency,
        source_reliability=source_reliability,
        history_ambiguity=history_ambiguity,
        overall_confidence=overall_confidence,
        is_blocked=is_blocked,
        has_rollback=has_rollback,
        rollback_commits=rollback_commits,
        limitations=limitations,
    )

    return {
        "score": score,
        "grade": grade,
        "coverage": coverage_pct,
        "consistency": consistency,
        "ambiguity": ambiguity_desc,
        "confidence": overall_confidence,
        "inconsistent_pairs": inconsistent_pairs,
        "total_events": total,
        "reverts_count": reverts,
        "has_diff": has_diff,
        "has_refs": has_refs,
        "has_message": has_message,
        "has_context": has_context,
        "strength": f"{grade} [{score}/12점]",

        # Confidence Model v2 확장 필드
        "availability": availability,
        "source_reliability": source_reliability,
        "history_ambiguity": history_ambiguity,
        "is_blocked": is_blocked,
        "has_rollback": has_rollback,
        "limitations": limitations,
        "report": report,
    }


def build_timeline(
    commits,
    repo_info,
    fetch_ref_func,
    fetch_commit_prs_func=None,
):
    """
    Commit 목록을 오래된 순서의 Timeline으로 구성하고
    GitHub PR/Issue Evidence를 연결한다.

    조회 우선순위:
    1. Commit SHA 기반 PR 조회
    2. SHA 기반 PR이 확인되지 않은 경우 Commit message의
       #번호를 기반으로 Issue/PR 조회
    """
    timeline = list(
        reversed(commits)
    )

    for idx, item in enumerate(timeline):

        if idx == 0:
            item["type"] = "🌱 FIRST OBSERVED"

        else:
            item["type"] = classify_commit(
                item["message"],
                item.get(
                    "is_revert",
                    False,
                ),
            )

        ref_details = []
        ref_items = []

        found_by_sha = False

        # -----------------------------------------------------
        # 1. Commit SHA -> GitHub PR
        # -----------------------------------------------------
        if (
            repo_info
            and fetch_commit_prs_func
            and item.get("hash")
        ):
            owner, repo_name = repo_info

            prs = fetch_commit_prs_func(
                owner,
                repo_name,
                item["hash"],
            )

            if prs:
                for pr in prs:
                    ref_items.append(pr)

                    pr_title = pr.get(
                        "title",
                        "",
                    )

                    title_part = (
                        f" ('{pr_title}')"
                        if pr_title
                        else ""
                    )

                    ref_details.append(
                        f"PR #{pr.get('number')}"
                        f"{title_part}"
                    )

                found_by_sha = True

        # -----------------------------------------------------
        # 2. Commit message #number fallback
        # -----------------------------------------------------
        if not found_by_sha and repo_info:
            owner, repo_name = repo_info

            for num in item.get(
                "refs",
                [],
            ):
                res = fetch_ref_func(
                    owner,
                    repo_name,
                    num,
                )

                if (
                    isinstance(res, dict)
                    and res.get("status") == "SUCCESS"
                ):
                    ref_type = res.get(
                        "type",
                        "REF",
                    )

                    title = res.get(
                        "title",
                        "",
                    )

                    label = (
                        f"{ref_type} #{num}"
                    )

                    if title:
                        ref_details.append(
                            f"{label} ('{title}')"
                        )
                    else:
                        ref_details.append(
                            label
                        )

                    ref_items.append(
                        res
                    )

                elif (
                    isinstance(res, dict)
                    and res.get("status")
                    == "NOT_FOUND"
                ):
                    ref_details.append(
                        f"REF #{num} [NOT FOUND]"
                    )

                    ref_items.append(
                        res
                    )

                elif (
                    isinstance(res, dict)
                    and res.get("title")
                ):
                    ref_details.append(
                        f"#{num} "
                        f"('{res['title']}')"
                    )

                    ref_items.append(
                        res
                    )

                else:
                    ref_details.append(
                        f"#{num}"
                    )

                    ref_items.append(
                        {
                            "number": num,
                            "title": "",
                            "type": "REF",
                            "url": "",
                            "body_summary": "",
                            "labels": [],
                        }
                    )

        item["ref_details"] = ref_details
        item["ref_items"] = ref_items

    stats = calculate_evidence_strength(
        timeline
    )

    return timeline, stats