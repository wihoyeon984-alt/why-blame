import urllib.request
import urllib.error
import json

# 중복 API 호출 방지용 메모리 캐시
_cache = {}

def fetch_ref_info(owner, repo, number):
    """
    GitHub Issue 또는 Pull Request 메타데이터를 구조화하여 반환합니다.
    - PR과 Issue 구분 ('type': 'PR' | 'ISSUE')
    - 에러 분기 처리 (404 Not Found, 403 Rate Limit, 네트워크 오류)
    - 중복 호출 방지 캐싱
    """
    cache_key = f"{owner}/{repo}#{number}"
    if cache_key in _cache:
        return _cache[cache_key]

    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Why-Blame-Client"
    }

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=3.0) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                
                # pull_request 필드 존재 여부로 PR과 Issue 구분
                is_pr = "pull_request" in data
                
                result = {
                    "status": "SUCCESS",
                    "number": number,
                    "type": "PR" if is_pr else "ISSUE",
                    "title": data.get("title", ""),
                    "state": data.get("state", "closed"),
                    "url": data.get("html_url", "")
                }
                _cache[cache_key] = result
                return result

    except urllib.error.HTTPError as e:
        if e.code == 404:
            result = {"status": "NOT_FOUND", "number": number, "type": "UNKNOWN", "title": "", "state": None, "url": None}
        elif e.code == 403:
            result = {"status": "RATE_LIMIT", "number": number, "type": "UNKNOWN", "title": "", "state": None, "url": None}
        else:
            result = {"status": f"HTTP_ERROR_{e.code}", "number": number, "type": "UNKNOWN", "title": "", "state": None, "url": None}
        _cache[cache_key] = result
        return result

    except (urllib.error.URLError, TimeoutError):
        return {"status": "NETWORK_ERROR", "number": number, "type": "UNKNOWN", "title": "", "state": None, "url": None}
    except Exception:
        return {"status": "UNKNOWN_ERROR", "number": number, "type": "UNKNOWN", "title": "", "state": None, "url": None}

# 하위 호환성을 위한 별칭 함수들
fetch_reference = fetch_ref_info
fetch_title = lambda owner, repo, num: fetch_ref_info(owner, repo, num).get("title", "")