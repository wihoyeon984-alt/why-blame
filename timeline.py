from consistency import check_evidence_consistency

def classify_commit(message, is_revert=False):
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

    if any(k in m_low for k in ["fix", "bug", "patch", "resolve", "prevent"]):
        return "🐛 BUG FIX"
    if any(k in m_low for k in ["feat", "add", "implement"]):
        return "✨ FEATURE"
    if any(k in m_low for k in ["refactor", "cleanup"]):
        return "🧹 REFACTOR"

    return "🔧 UPDATE"


def calculate_evidence_strength(timeline):
    """
    [4차원 신뢰도 모델]
    1. Coverage: Commit(2) + Diff(2) + Valid PR/Issue(3) + Metadata(2) + Context/Revert(3) = 12점
    2. Consistency: HIGH / MODERATE / INCONSISTENT
    3. Ambiguity: Revert 발생 여부를 독립된 복잡도 신호로 분리
    4. Confidence: Coverage + Consistency 종합 판정
    """
    score = 0
    total = len(timeline)
    reverts = sum(1 for t in timeline if t.get("is_revert"))
    has_diff = any(len(t.get("diff_lines", [])) > 0 for t in timeline)
    
    # NOT_FOUND 참조는 증거로 인정하지 않음
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

    # 배점 계산 (PR 본문 맥락 또는 검증 이력이 있으면 증거 가용성 +3 부여)
    if has_message:
        score += 2
    if has_diff:
        score += 2
    if has_refs:
        score += 3
    if has_fetched:
        score += 2
    if has_context or reverts > 0:
        score += 3

    # 12점 만점 상한
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

    # 이력 복잡도 (Ambiguity) 분리
    ambiguity = f"COMPLEX ({reverts}회 롤백 이력)" if reverts > 0 else "LOW (선형 이력)"
    coverage_pct = f"{int(score / 12 * 100)}%"

    # Consistency 평가
    has_inconsistent = False
    has_consistent = False
    inconsistent_pairs = []

    for t in timeline:
        c_msg = t.get("message", "")
        for ref in t.get("ref_items", []):
            if ref.get("title") and ref.get("type") == "PR":
                chk = check_evidence_consistency(c_msg, ref.get("title", ""), ref.get("body_summary", ""))
                if chk["level"] == "INCONSISTENT":
                    has_inconsistent = True
                    inconsistent_pairs.append(f"Commit '{c_msg[:25]}' ↔ PR #{ref.get('number')} '{ref.get('title')[:25]}'")
                elif chk["level"] == "HIGH":
                    has_consistent = True

    if has_inconsistent:
        consistency = "INCONSISTENT"
        confidence = "LOW (증거 불일치)"
    elif has_consistent:
        consistency = "HIGH"
        confidence = grade
    else:
        consistency = "UNLINKED" if not has_refs else "MODERATE"
        confidence = grade

    return {
        "score": score,
        "grade": grade,
        "coverage": coverage_pct,
        "consistency": consistency,
        "ambiguity": ambiguity,
        "confidence": confidence,
        "inconsistent_pairs": inconsistent_pairs,
        "total_events": total,
        "reverts_count": reverts,
        "has_diff": has_diff,
        "has_refs": has_refs,
        "has_message": has_message,
        "has_context": has_context,
        "strength": f"{grade} [{score}/12점]"
    }


def build_timeline(commits, repo_info, fetch_ref_func, fetch_commit_prs_func=None):
    timeline = list(reversed(commits))

    for idx, item in enumerate(timeline):
        if idx == 0:
            item["type"] = "📍 FIRST OBSERVED"
        else:
            item["type"] = classify_commit(item["message"], item["is_revert"])

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