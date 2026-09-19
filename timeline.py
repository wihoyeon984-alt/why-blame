def classify_commit(message, is_revert=False):
    """
    Conventional Commits 프리픽스(feat:, fix: 등)를 최우선으로 인식합니다.
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

    # 일반 키워드 폴백
    if any(k in m_low for k in ["fix", "bug", "patch", "resolve", "prevent"]):
        return "🐛 BUG FIX"
    if any(k in m_low for k in ["feat", "add", "implement"]):
        return "✨ FEATURE"
    if any(k in m_low for k in ["refactor", "cleanup"]):
        return "🧹 REFACTOR"

    return "🔧 UPDATE"


def calculate_evidence_strength(timeline):
    """
    가중치 매트릭스 (총점 12점 만점)
    README 명세: 0-2 LOW, 3-4 WEAK, 5-7 MODERATE, 8-10 HIGH, 11+ VERY HIGH
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
        "strength": f"{grade} [{score}/12점]"
    }


def build_timeline(commits, repo_info, fetch_ref_func):
    timeline = list(reversed(commits))

    for idx, item in enumerate(timeline):
        if idx == 0:
            item["type"] = "🌱 BIRTH"
        else:
            item["type"] = classify_commit(item["message"], item["is_revert"])

        ref_details = []
        ref_items = []
        for num in item["refs"]:
            if repo_info:
                owner, repo_name = repo_info
                res = fetch_ref_func(owner, repo_name, num)
                
                # 구조화된 딕셔너리 응답 처리
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
                elif isinstance(res, str) and res:
                    ref_details.append(f"#{num} ('{res}')")
                    ref_items.append({"number": num, "title": res, "type": "REF", "url": ""})
                else:
                    ref_details.append(f"#{num}")
                    ref_items.append({"number": num, "title": "", "type": "REF", "url": ""})
            else:
                ref_details.append(f"#{num}")
                ref_items.append({"number": num, "title": "", "type": "REF", "url": ""})

        item["ref_details"] = ref_details
        item["ref_items"] = ref_items

    stats = calculate_evidence_strength(timeline)
    return timeline, stats