import re

STOPWORDS = {
    "fix", "fixes", "fixed", "feat", "feature", "features", "add", "added", "adding",
    "update", "updated", "updating", "test", "tests", "chore", "refactor", "cleanup",
    "the", "a", "an", "in", "on", "for", "of", "to", "and", "or", "is", "with",
    "from", "by", "after", "before", "this", "that", "code", "change", "changes",
    "bug", "issue", "pr", "pull", "request", "commit", "verify", "verifying", "check",
    "make", "handling", "improve", "improved", "support", "using", "work", "status"
}

# 도메인 유의어 클러스터 (Semantic Domain Clusters)
SYNONYM_CLUSTERS = [
    {"payment", "billing", "charge", "checkout", "invoice", "pay", "pricing", "refund"},
    {"auth", "authentication", "login", "logout", "token", "session", "permission", "oauth", "credential"},
    {"cache", "caching", "redis", "memcached"},
    {"db", "database", "sql", "postgres", "mysql", "model", "query", "migration", "orm"},
    {"cancel", "cancellation", "revoke", "abort", "terminate"},
    {"user", "account", "profile", "member"},
    {"network", "http", "api", "endpoint", "connection", "socket", "timeout", "gateway"}
]

def extract_domain_tokens(text):
    if not text:
        return set()
    clean = re.sub(r"[^a-zA-Z0-9가-힣\s]", " ", text.lower())
    tokens = [t.strip() for t in clean.split() if len(t.strip()) >= 3]
    return set(t for t in tokens if t not in STOPWORDS)

def expand_synonyms(tokens):
    expanded = set(tokens)
    for tok in tokens:
        for cluster in SYNONYM_CLUSTERS:
            if tok in cluster:
                expanded.update(cluster)
    return expanded

def check_evidence_consistency(commit_msg, pr_title, pr_body=""):
    """
    커밋 메시지와 PR 간의 도메인 일치도를 다단계로 판별합니다.
    - Title: Strong evidence
    - Body: Supporting evidence
    - 단어 1개 우연 일치 시 MODERATE로 안전 판정 (False HIGH 방지)
    - 도메인 유의어 클러스터 지원 (cache <-> redis, payment <-> billing)
    """
    if not pr_title:
        return {"level": "UNLINKED", "score": 0.0, "reason": "연관 PR 없음"}

    c_tokens = extract_domain_tokens(commit_msg)
    p_title_tokens = extract_domain_tokens(pr_title)
    p_body_tokens = extract_domain_tokens(pr_body)

    if not c_tokens:
        return {"level": "MODERATE", "score": 0.5, "reason": "커밋 메시지 단서 부족 (PR 기준 참조)"}

    exact_title_match = c_tokens & p_title_tokens
    c_expanded = expand_synonyms(c_tokens)
    p_expanded = expand_synonyms(p_title_tokens)
    synonym_title_match = c_expanded & p_expanded

    coverage = len(exact_title_match) / len(c_tokens) if c_tokens else 0.0

    # 1. 강한 일치 (HIGH): 과반수 토큰 일치 or 단일 토큰 커밋의 정확 일치 or 유의어 일치
    if (coverage > 0.5 and len(exact_title_match) >= 2) or (len(c_tokens) == 1 and exact_title_match):
        matched_str = ", ".join(sorted(exact_title_match))
        return {
            "level": "HIGH",
            "score": 1.0,
            "reason": f"핵심 도메인 일치 ({matched_str})"
        }
    elif synonym_title_match and not (exact_title_match and len(c_tokens) >= 2 and coverage <= 0.5):
        matched_str = ", ".join(sorted(synonym_title_match))
        return {
            "level": "HIGH",
            "score": 0.9,
            "reason": f"도메인 유의어 일치 ({matched_str})"
        }

    # 2. 부분 일치 (MODERATE / AMBIGUOUS): 단어 1개만 스치거나 본문에만 단서가 있는 경우
    exact_body_match = c_tokens & p_body_tokens
    if exact_title_match or exact_body_match:
        matched = exact_title_match or exact_body_match
        matched_str = ", ".join(sorted(matched))
        return {
            "level": "MODERATE",
            "score": 0.5,
            "reason": f"부분 맥락 일치 ({matched_str}) - 추가 검토 필요"
        }

    # 3. 상충 (INCONSISTENT)
    return {
        "level": "INCONSISTENT",
        "score": 0.0,
        "reason": f"맥락 상충 (커밋: {sorted(c_tokens)} vs PR: {sorted(p_title_tokens)})"
    }