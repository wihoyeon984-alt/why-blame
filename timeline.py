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
    score = 0
    total = len(timeline)
    reverts = sum(1 for t in timeline if t.get("is_revert"))
    has_diff = any(len(t.get("diff_lines", [])) > 0 for t in timeline)
    has_refs = any(len(t.get("refs", [])) > 0 or len(t.get("ref_items", [])) > 0 for t in timeline)
    has_fetched = any(
        any(ref.get("title") for ref in t.get("ref_items", []))
        or any("'" in r for r in t.get("ref_details", []))
        for t in timeline
    )
    has_message = total > 0 and any(len(t.get("message", "")) > 5 for t in timeline)

    if has_message:
        score += 2
    if has_diff:
        score += 2
    if has_refs:
        score += 3
    if has_fetched:
        score += 2
    if reverts > 0:
        score += 3

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

    return {
        "score": score,
        "grade": grade,
        "total_events": total,
        "reverts_count": reverts,
        "has_diff": has_diff,
        "has_refs": has_refs,
        "has_message": has_message,
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

        # 1. 커밋 해시(SHA)로 실제 연결된 GitHub PR 우선 탐색
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

        # 2. SHA 탐색 결과가 없을 경우 커밋 메시지의 #번호로 폴백 조회
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