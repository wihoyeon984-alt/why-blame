from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
from consistency import check_evidence_consistency


@dataclass
class ConfidenceReport:
    """Confidence Model v2 평가 결과 데이터 클래스"""
    availability: str         # HIGH, MODERATE, LOW
    consistency: str          # HIGH, MODERATE, INCONSISTENT, UNLINKED
    source_reliability: str   # HIGH, MODERATE, LOW
    history_ambiguity: str    # LOW, MEDIUM, HIGH
    overall_confidence: str   # VERY HIGH, HIGH, MEDIUM, LOW, WEAK
    is_blocked: bool = False
    has_rollback: bool = False
    rollback_commits: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


def classify_commit(message: str, is_revert: bool = False) -> str:
    m_low = message.strip().lower()
    if is_revert or m_low.startswith("revert"):
        return "🔄 REVERT"

    prefix = m_low.split(":")[0].strip() if ":" in m_low else ""
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

    if any(k in m_low for k in ["fix", "bug", "patch", "resolve", "prevent"]):
        return "🐛 BUG FIX"
    if any(k in m_low for k in ["feat", "add", "implement"]):
        return "✨ FEATURE"
    if any(k in m_low for k in ["refactor", "cleanup"]):
        return "♻️ REFACTOR"

    return "📦 UPDATE"


def calculate_availability(has_message: bool, has_diff: bool, has_refs: bool, has_context: bool) -> str:
    """Evidence Availability (증거 가용성) 평가"""
    if has_message and has_diff and has_refs and has_context:
        return "HIGH"
    if has_message and (has_diff or has_refs):
        return "MODERATE"
    return "LOW"


def calculate_consistency(timeline: list, has_refs: bool) -> Tuple[str, List[str]]:
    """Evidence Consistency (맥락 일관성) 평가"""
    has_inconsistent = False
    has_consistent = False
    inconsistent_pairs = []

    for t in timeline:
        c_msg = t.get("message", "")
        for ref in t.get("ref_items", []):
            if ref.get("title") and ref.get("type") == "PR":
                chk = check_evidence_consistency(c_msg, ref.get("title", ""), ref.get("body_summary", ""))
                if chk.get("level") == "INCONSISTENT":
                    has_inconsistent = True
                    inconsistent_pairs.append(f"Commit '{c_msg[:25]}' ↔ PR #{ref.get('number')} '{ref.get('title')[:25]}'")
                elif chk.get("level") == "HIGH":
                    has_consistent = True

    if has_inconsistent:
        return "INCONSISTENT", inconsistent_pairs
    if has_consistent:
        return "HIGH", []
    if not has_refs:
        return "UNLINKED", []
    return "MODERATE", []


def calculate_source_reliability(timeline: list, has_refs: bool) -> str:
    """Source Reliability (출처 신뢰도) 평가"""
    if not has_refs:
        return "LOW"

    has_verified_api = any(
        any(r.get("status") == "SUCCESS" and r.get("title") for r in t.get("ref_items", []))
        for t in timeline
    )
    if has_verified_api:
        return "HIGH"
    return "MODERATE"


def calculate_history_ambiguity(timeline: list, reverts_count: int) -> Tuple[str, bool, List[str]]:
    """History Ambiguity (이력 모호성) 평가: Revert 격리"""
    rollback_commits = [
        t.get("message", "") for t in timeline if t.get("is_revert") or t.get("message", "").strip().lower().startswith("revert")
    ]
    if reverts_count > 0 or len(rollback_commits) > 0:
        return "HIGH", True, rollback_commits
    if len(timeline) >= 3:
        return "MEDIUM", False, []
    return "LOW", False, []


def decide_overall_confidence(
    availability: str,
    consistency: str,
    source_reliability: str,
    history_ambiguity: str
) -> Tuple[str, bool, List[str]]:
    """
    Confidence 결정 매트릭스:
    1. INCONSISTENT                            -> LOW + WHY BLOCKED
    2. UNLINKED                                -> WEAK
    3. HIGH consistency + LOW availability     -> MODERATE
    4. HIGH consistency + MODERATE/HIGH avl    -> HIGH 또는 VERY HIGH
    5. Revert detected (Ambiguity == HIGH)     -> Confidence 상한선 MEDIUM (WHY는 허용)
    """
    limitations = []
    is_blocked = False

    if consistency == "INCONSISTENT":
        overall = "LOW (증거 불일치)"
        is_blocked = True
        limitations.append("증거 간 맥락 불일치로 인해 신뢰도가 낮으며 WHY 생성이 차단됩니다.")
    elif consistency == "UNLINKED":
        overall = "WEAK"
        limitations.append("연관 PR/Issue 증거가 연결되지 않아 코드 히스토리 신뢰도가 제한적입니다.")
    elif consistency == "HIGH":
        if availability == "LOW":
            overall = "MODERATE"
            limitations.append("증거 맥락은 일치하나 가용한 증거의 양(Availability)이 적습니다.")
        elif availability == "MODERATE":
            overall = "HIGH"
        else:  # HIGH availability
            if source_reliability == "HIGH":
                overall = "VERY HIGH"
            else:
                overall = "HIGH"
    else:  # MODERATE consistency
        if availability == "HIGH":
            overall = "HIGH"
        elif availability == "MODERATE":
            overall = "MODERATE"
        else:
            overall = "WEAK"

    # Revert / Ambiguity Cap (상한선 MEDIUM 제한)
    if history_ambiguity == "HIGH":
        limitations.append("Rollback history increases ambiguity.")
        if overall in ["VERY HIGH", "HIGH"]:
            overall = "MEDIUM"

    return overall, is_blocked, limitations


def calculate_evidence_strength(timeline: list) -> dict:
    """
    Confidence Model v2 통합 함수
    (기존 calculate_evidence_strength 하위 호환성 유지)
    """
    total = len(timeline)
    reverts = sum(1 for t in timeline if t.get("is_revert"))
    has_diff = any(len(t.get("diff_lines", [])) > 0 for t in timeline)

    # 유효 참조 확인 (NOT_FOUND 제외)
    valid_refs_exist = False
    for t in timeline:
        if t.get("ref_items"):
            if any(r.get("status") == "SUCCESS" or (r.get("title") and r.get("status") != "NOT_FOUND") for r in t.get("ref_items", [])):
                valid_refs_exist = True
        elif t.get("refs"):
            valid_refs_exist = True

    has_refs = valid_refs_exist
    has_fetched = any(
        any(ref.get("title") for ref in t.get("ref_items", []))
        or any("'" in r for r in t.get("ref_details", []))
        for t in timeline
    )
    has_context = any(
        any(ref.get("body_summary") for ref in t.get("ref_items", []))
        for t in timeline
    )
    has_message = total > 0 and any(len(t.get("message", "")) > 5 for t in timeline)

    # 1. 4대 축 개별 평가
    availability = calculate_availability(has_message, has_diff, has_refs, has_context)
    consistency, inconsistent_pairs = calculate_consistency(timeline, has_refs)
    source_reliability = calculate_source_reliability(timeline, has_refs)
    history_ambiguity, has_rollback, rollback_commits = calculate_history_ambiguity(timeline, reverts)

    # 2. 최종 Confidence 산출 (결정 매트릭스)
    overall_confidence, is_blocked, limitations = decide_overall_confidence(
        availability, consistency, source_reliability, history_ambiguity
    )

    # 3. 레거시 점수 호환성 계산 (revert 가산점 완전 제외)
    score = 0
    if has_message:
        score += 2
    if has_diff:
        score += 2
    if has_refs:
        score += 3
    if has_fetched:
        score += 2
    if has_context:  # reverts > 0 제거
        score += 3

    score = min(12, score)

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

    ambiguity_desc = f"COMPLEX ({reverts}회 롤백 이력)" if has_rollback else (
        "MODERATE (다중 이력)" if history_ambiguity == "MEDIUM" else "LOW (단방향 이력)"
    )
    coverage_pct = f"{int(score / 12 * 100)}%"

    report = ConfidenceReport(
        availability=availability,
        consistency=consistency,
        source_reliability=source_reliability,
        history_ambiguity=history_ambiguity,
        overall_confidence=overall_confidence,
        is_blocked=is_blocked,
        has_rollback=has_rollback,
        rollback_commits=rollback_commits,
        limitations=limitations
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
        # v2 확장 필드
        "availability": availability,
        "source_reliability": source_reliability,
        "history_ambiguity": history_ambiguity,
        "is_blocked": is_blocked,
        "has_rollback": has_rollback,
        "limitations": limitations,
        "report": report
    }


def build_timeline(commits, repo_info, fetch_ref_func, fetch_commit_prs_func=None):
    timeline = list(reversed(commits))

    for idx, item in enumerate(timeline):
        if idx == 0:
            item["type"] = "🌱 FIRST OBSERVED"
        else:
            item["type"] = classify_commit(item["message"], item.get("is_revert", False))

        ref_details = []
        ref_items = []
        found_by_sha = False

        if repo_info and fetch_commit_prs_func and item.get("hash"):
            owner, repo_name = repo_info
            prs = fetch_commit_prs_func(owner, repo_name, item["hash"])
            if prs:
                for pr in prs:
                    ref_items.append(pr)
                    p_title = pr.get("title", "")
                    title_part = f" ('{p_title}')" if p_title else ""
                    ref_details.append(f"PR #{pr.get('number')}{title_part}")
                found_by_sha = True

        if not found_by_sha and repo_info:
            owner, repo_name = repo_info
            for num in item.get("refs", []):
                res = fetch_ref_func(owner, repo_name, num)
                if isinstance(res, dict) and res.get("status") == "SUCCESS":
                    ref_type = res.get("type", "REF")
                    title = res.get("title", "")
                    label = f"{ref_type} #{num}"
                    if title:
                        ref_details.append(f"{label} ('{title}')")
                    else:
                        ref_details.append(label)
                    ref_items.append(res)
                elif isinstance(res, dict) and res.get("status") == "NOT_FOUND":
                    ref_details.append(f"REF #{num} [NOT FOUND]")
                    ref_items.append(res)
                elif isinstance(res, dict) and res.get("title"):
                    ref_details.append(f"#{num} ('{res['title']}')")
                    ref_items.append(res)
                else:
                    ref_details.append(f"#{num}")
                    ref_items.append({"number": num, "title": "", "type": "REF", "url": "", "body_summary": "", "labels": []})

        item["ref_details"] = ref_details
        item["ref_items"] = ref_items

    stats = calculate_evidence_strength(timeline)
    return timeline, stats
