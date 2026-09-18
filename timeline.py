def classify_commit(message, is_revert=False):
    """
    Conventional Commits 프리픽스(feat:, fix: 등)를 최우선으로 인식합니다.
    예: 'feat: fix login UI' -> 'fix' 단어가 있어도 접두어가 feat이므로 FEATURE로 분류
    """
    m_low = message.strip().lower()
    if is_revert or m_low.startswith("revert"):
        return "↩ REVERT"

    prefix = m_low.split(":")[0].strip() if ":" in m_low else ""
    if prefix in ["feat", "feature"]:
        return "✨ FEATURE"
    if prefix in ["fix", "bug", "hotfix", "patch"]:
        return "🐛 BUG FIX"
    if prefix in ["revert", "rollback"]:
        return "↩ REVERT"
    if prefix in ["refactor", "cleanup"]:
        return "🧹 REFACTOR"
    if prefix in ["test", "tests"]:
        return "🧪 TEST"
    if prefix in ["docs"]:
        return "📝 DOCS"
    if prefix in ["perf"]:
        return "⚡ PERF"
    if prefix in ["sec", "security"]:
        return "🔒 SECURITY"

    # 접두어가 없는 일반 커밋용 키워드 폴백
    if any(k in m_low for k in ["fix", "bug", "patch", "resolve", "prevent"]):
        return "🐛 BUG FIX"
    if any(k in m_low for k in ["feat", "add", "implement"]):
        return "✨ FEATURE"
    if any(k in m_low for k in ["refactor", "cleanup"]):
        return "🧹 REFACTOR"

    return "🔧 UPDATE"


def calculate_evidence_strength(timeline):
    """
    리뷰어 권장 8개 항목 가중치 매트릭스 (총점 12점 만점)
    - Commit 메시지 (+1)
    - 코드 Diff 존재 (+2)
    - Issue/PR 참조 번호 (+3)
    - GitHub 실제 제목 확인 (+2)
    - Revert 이력 (+3)
    """
    score = 0
    total = len(timeline)
    reverts = sum(1 for t in timeline if t.get("is_revert"))
    has_diff = any(len(t.get("diff_lines", [])) > 0 for t in timeline)
    has_refs = any(len(t.get("refs", [])) > 0 for t in timeline)
    has_fetched = any(any("'" in r for r in t.get("ref_details", [])) for t in timeline)

    if total > 0 and any(len(t.get("message", "")) > 5 for t in timeline):
        score += 1
    if has_diff:
        score += 2
    if has_refs:
        score += 3
    if has_fetched:
        score += 2
    if reverts > 0:
        score += 3

    if score >= 9:
        grade = "VERY HIGH (매우 강력한 근거)"
    elif score >= 6:
        grade = "HIGH (명확한 근거)"
    elif score >= 4:
        grade = "MODERATE (보통)"
    elif score >= 2:
        grade = "WEAK (약한 근거)"
    else:
        grade = "LOW (근거 불충분)"

    return {
        "score": score,
        "grade": grade,
        "total_events": total,
        "reverts_count": reverts,
        "has_diff": has_diff,
        "has_refs": has_refs,
        "strength": f"{grade} [{score}/12점]"
    }


def build_timeline(commits, repo_info, fetch_title_func):
    timeline = list(reversed(commits))

    for idx, item in enumerate(timeline):
        if idx == 0:
            item["type"] = "🌱 BIRTH"
        else:
            item["type"] = classify_commit(item["message"], item["is_revert"])

        ref_details = []
        for num in item["refs"]:
            if repo_info:
                owner, repo_name = repo_info
                title = fetch_title_func(owner, repo_name, num)
                if title:
                    ref_details.append(f"#{num} ('{title}')")
                else:
                    ref_details.append(f"#{num}")
            else:
                ref_details.append(f"#{num}")
        item["ref_details"] = ref_details

    stats = calculate_evidence_strength(timeline)
    return timeline, stats