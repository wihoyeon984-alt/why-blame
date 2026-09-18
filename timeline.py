def classify_commit(message, is_revert):
    """커밋 메시지와 롤백 여부를 분석하여 정확한 카테고리를 분류합니다."""
    m = message.lower()
    
    # 1. 롤백 감지
    if is_revert or "rollback" in m:
        return "↩ REVERT"
    
    # 2. 보안 감지
    if any(k in m for k in ["sec", "security", "vuln", "cve", "auth", "token"]):
        return "🔒 SECURITY"
        
    # 3. 버그 수정 감지 (단어 확장)
    if any(k in m for k in ["fix", "bug", "hotfix", "patch", "resolve", "correct", "prevent", "issue"]):
        return "🐛 BUG FIX"
        
    # 4. 기능 추가 감지
    if any(k in m for k in ["feat", "feature", "add", "implement", "introduce", "support"]):
        return "✨ FEATURE"
        
    # 5. 성능 개선 감지
    if any(k in m for k in ["perf", "performance", "optimize", "speed", "fast"]):
        return "⚡ PERF"
        
    # 6. 리팩터링 감지
    if any(k in m for k in ["refactor", "cleanup", "clean up", "restructure", "rename", "style"]):
        return "🧹 REFACTOR"
        
    # 7. 문서 및 테스트
    if any(k in m for k in ["docs", "readme", "comment"]):
        return "📝 DOCS"
    if any(k in m for k in ["test", "tests"]):
        return "🧪 TEST"
        
    return "🔧 UPDATE"


def calculate_evidence_strength(timeline):
    """
    증거 가중치 매트릭스에 따라 합리적인 점수를 계산합니다.
    - Commit 기본 증거: +1점
    - 실제 Code Diff 존재: +2점
    - Revert(롤백) 이력 존재: +3점
    - Linked Issue/PR 참조 존재: +3점
    """
    score = 0
    total_events = len(timeline)
    reverts_count = sum(1 for item in timeline if item["is_revert"])
    
    # 기본 커밋 증거 점수
    if total_events > 0:
        score += 1
    if total_events >= 3:
        score += 1
        
    # Diff 증거 점수
    has_diff = any(len(item.get("diff_lines", [])) > 0 for item in timeline)
    if has_diff:
        score += 2
        
    # 롤백 증거 점수 (롤백은 코드의 필요성을 증명하는 매우 강력한 팩트)
    if reverts_count > 0:
        score += 3
        
    # 이슈/PR 참조 증거 점수
    has_refs = any(len(item.get("refs", [])) > 0 for item in timeline)
    if has_refs:
        score += 3

    # 점수대별 등급 산출
    if score >= 8:
        strength = "VERY HIGH (매우 강력한 근거)"
    elif score >= 5:
        strength = "HIGH (명확한 근거)"
    elif score >= 3:
        strength = "MEDIUM (보통)"
    else:
        strength = "LOW (증거 불충분)"
        
    return {
        "total_events": total_events,
        "reverts_count": reverts_count,
        "strength": strength,
        "score": score
    }


def build_timeline(commits, repo_info, fetch_title_func):
    """커밋들을 시간순으로 정렬하고, 각 이벤트의 성격과 GitHub 맥락을 결합합니다."""
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