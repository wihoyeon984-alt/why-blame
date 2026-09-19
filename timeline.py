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

    if any(
        keyword in m_low
        for keyword in ["fix", "bug", "patch", "resolve", "prevent"]
    ):
        return "🐛 BUG FIX"

    if any(
        keyword in m_low
        for keyword in ["feat", "add", "implement"]
    ):
        return "✨ FEATURE"

    if any(
        keyword in m_low
        for keyword in ["refactor", "cleanup"]
    ):
        return "🧹 REFACTOR"

    return "🔧 UPDATE"


def calculate_evidence_strength(timeline):
    score = 0
    total = len(timeline)

    reverts = sum(
        1 for item in timeline
        if item.get("is_revert")
    )

    has_diff = any(
        len(item.get("diff_lines", [])) > 0
        for item in timeline
    )

    # 실제 GitHub 객체가 확인된 경우만 refs 증거로 인정
    has_refs = any(
        any(
            isinstance(ref, dict)
            and ref.get("status") == "SUCCESS"
            for ref in item.get("ref_items", [])
        )
        for item in timeline
    )

    has_fetched = any(
        any(
            isinstance(ref, dict)
            and ref.get("status") == "SUCCESS"
            and ref.get("title")
            for ref in item.get("ref_items", [])
        )
        for item in timeline
    )

    has_message = (
        total > 0
        and any(
            len(item.get("message", "")) > 5
            for item in timeline
        )
    )

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


def build_timeline(
    commits,
    repo_info,
    fetch_ref_func,
    fetch_commit_prs_func=None
):
    timeline = list(reversed(commits))

    for idx, item in enumerate(timeline):

        if idx == 0:
            item["type"] = "📍 FIRST OBSERVED"
        else:
            item["type"] = classify_commit(
                item["message"],
                item["is_revert"]
            )

        ref_details = []
        ref_items = []

        found_by_sha = False

        # =========================================================
        # 1. SHA → 실제 GitHub PR
        # =========================================================
        if (
            repo_info
            and fetch_commit_prs_func
            and item.get("hash")
        ):
            owner, repo_name = repo_info

            prs = fetch_commit_prs_func(
                owner,
                repo_name,
                item["hash"]
            )

            if prs:
                for pr in prs:
                    ref_items.append(pr)

                    number = pr.get("number")
                    title = pr.get("title", "")

                    if title:
                        ref_details.append(
                            f"PR #{number} ('{title}')"
                        )
                    else:
                        ref_details.append(
                            f"PR #{number}"
                        )

                found_by_sha = True

        # =========================================================
        # 2. SHA → PR이 없으면 커밋 메시지의 #번호 조회
        # =========================================================
        if not found_by_sha and repo_info:

            owner, repo_name = repo_info

            for num in item.get("refs", []):

                result = fetch_ref_func(
                    owner,
                    repo_name,
                    num
                )

                # 실제 GitHub Issue / PR
                if (
                    isinstance(result, dict)
                    and result.get("status") == "SUCCESS"
                ):
                    ref_type = result.get(
                        "type",
                        "REF"
                    )

                    title = result.get(
                        "title",
                        ""
                    )

                    if title:
                        ref_details.append(
                            f"{ref_type} #{num} ('{title}')"
                        )
                    else:
                        ref_details.append(
                            f"{ref_type} #{num}"
                        )

                    ref_items.append(result)

                # GitHub에 존재하지 않는 번호
                elif (
                    isinstance(result, dict)
                    and result.get("status") == "NOT_FOUND"
                ):
                    ref_details.append(
                        f"REF #{num} [NOT FOUND]"
                    )

                    ref_items.append({
                        "status": "NOT_FOUND",
                        "number": num,
                        "title": "",
                        "type": "UNKNOWN",
                        "url": ""
                    })

                # Rate limit
                elif (
                    isinstance(result, dict)
                    and result.get("status") == "RATE_LIMIT"
                ):
                    ref_details.append(
                        f"REF #{num} [RATE LIMIT]"
                    )

                    ref_items.append(result)

                # 기타 오류
                else:
                    status = (
                        result.get("status", "UNKNOWN")
                        if isinstance(result, dict)
                        else "UNKNOWN"
                    )

                    ref_details.append(
                        f"REF #{num} [{status}]"
                    )

                    ref_items.append({
                        "status": status,
                        "number": num,
                        "title": "",
                        "type": "UNKNOWN",
                        "url": ""
                    })

        item["ref_details"] = ref_details
        item["ref_items"] = ref_items

    stats = calculate_evidence_strength(timeline)

    return timeline, stats