import urllib.request
import json

# 1. API 중복 호출을 막는 메모리 캐시 딕셔너리
_cache = {}

def fetch_ref_info(owner, repo, number):
    """
    GitHub API를 호출하여 (타입, 제목) 튜플을 반환합니다.
    - 캐시 적용: 동일 번호 재호출 시 네트워크 요청 생략
    - 🔀 PR과 🐛 Issue를 'pull_request' 필드로 정밀 구분
    """
    cache_key = f"{owner}/{repo}#{number}"
    if cache_key in _cache:
        return _cache[cache_key]

    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}"
    req = urllib.request.Request(url, headers={"User-Agent": "Why-Blame-App"})
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            title = data.get("title", "")
            
            # [핵심] 응답 JSON에 'pull_request' 키가 있으면 PR, 없으면 Issue!
            kind = "🔀 PR" if "pull_request" in data else "🐛 Issue"
            result = (kind, title)
            _cache[cache_key] = result
            return result
    except Exception:
        _cache[cache_key] = (None, None)
        return (None, None)