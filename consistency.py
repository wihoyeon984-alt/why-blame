import re

# Git 및 일반적인 불용어(Stopwords)
STOPWORDS = {
    "fix", "fixes", "fixed", "feat", "feature", "features", "add", "added", "adding",
    "update", "updated", "updating", "test", "tests", "chore", "refactor", "cleanup",
    "the", "a", "an", "in", "on", "for", "of", "to", "and", "or", "is", "with",
    "from", "by", "after", "before", "this", "that", "code", "change", "changes",
    "bug", "issue", "pr", "pull", "request", "commit", "verify", "verifying", "check"
}

def extract_domain_tokens(text):
    """텍스트에서 불용어를 제외한 유의미한 도메인 어휘 토큰(3글자 이상)을 추출합니다."""
    if not text:
        return set()
    clean = re.sub(r"[^a-zA-Z0-9가-힣\s]", " ", text.lower())
    tokens = [t.strip() for t in clean.split() if len(t.strip()) >= 3]
    return set(t for t in tokens if t not in STOPWORDS)

def check_evidence_consistency(commit_msg, pr_title, pr_body=""):
    """
    커밋 메시지와 연관 PR 간의 맥락 일치도를 판별합니다.
    - HIGH: 핵심 도메인 어휘가 일치함
    - MODERATE: 커밋 메시지가 짧으나 PR 맥락이 존재함
    - INCONSISTENT: 서로 전혀 다른 주제를 다루고 있어 상충됨
    - UNLINKED: 연관 PR이 없음
    """
    if not pr_title:
        return {"level": "UNLINKED", "score": 0.0, "reason": "연관 PR 없음"}

    c_tokens = extract_domain_tokens(commit_msg)
    p_tokens = extract_domain_tokens(pr_title)
    if pr_body:
        p_tokens.update(extract_domain_tokens(pr_body))

    if not c_tokens:
        return {"level": "MODERATE", "score": 0.5, "reason": "커밋 메시지 단서 부족 (PR 기준 참조)"}

    intersection = c_tokens & p_tokens
    if intersection:
        matched_str = ", ".join(sorted(intersection))
        return {
            "level": "HIGH",
            "score": 1.0,
            "reason": f"핵심 도메인 키워드 일치 ({matched_str})"
        }
    else:
        return {
            "level": "INCONSISTENT",
            "score": 0.0,
            "reason": f"맥락 불일치 (커밋: {sorted(c_tokens)} vs PR: {sorted(p_tokens)})"
        }