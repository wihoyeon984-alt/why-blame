def build_timeline(commits, repo_info, fetch_title_func):
    """커밋들을 시간순으로 뒤집고, 이벤트 성격과 GitHub 제목을 결합합니다."""
    timeline = list(reversed(commits))

    for idx, item in enumerate(timeline):
        msg_low = item["message"].lower()
        if idx == 0:
            item["type"] = "🌱 BIRTH"
        elif item["is_revert"]:
            item["type"] = "↩ REVERT"
        elif "fix" in msg_low or "bug" in msg_low:
            item["type"] = "🐛 BUG FIX"
        elif "feat" in msg_low:
            item["type"] = "✨ FEATURE"
        else:
            item["type"] = "🔧 UPDATE"

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

    total_events = len(timeline)
    reverts_count = sum(1 for item in timeline if item["is_revert"])
    has_refs = any(len(item["refs"]) > 0 for item in timeline)

    if total_events >= 3 or (has_refs and reverts_count > 0):
        strength = "STRONG"
    elif total_events >= 2 or has_refs:
        strength = "MODERATE"
    else:
        strength = "WEAK"

    stats = {
        "total_events": total_events,
        "reverts_count": reverts_count,
        "strength": strength,
    }
    return timeline, stats