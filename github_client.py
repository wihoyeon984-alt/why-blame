import urllib.request
import urllib.error
import json

# 중복 API 호출 방지용 메모리 캐시
_cache = {}

def fetch_ref_info(owner, repo, number):
    """
    GitHub Issue 또는 Pull Request 메타데이터를 구조화하여 반환합니다.
    - PR과 Issue 구분 ('type': 'PR' | 'ISSUE')
    - 본문(Body) 핵심 요약문 및 라벨(Labels) 추출
    - 상태 코드별 에러 분기 및 캐싱
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
                
                # pull_request 필드 유무로 PR과 일반 Issue 구분
                is_pr = "pull_request" in data
                
                # 본문(Body)에서 첫 1~2문장의 핵심 맥락 요약 추출
                body_raw = data.get("body") or ""
                summary_lines = [l.strip() for l in body_raw.splitlines() if l.strip() and not l.startswith("#")]
                body_summary = " ".join(summary_lines[:2])[:120] if summary_lines else ""
                
                # 라벨 추출
                labels = [l.get("name") for l in data.get("labels", []) if isinstance(l, dict)]

                result = {
                    "status": "SUCCESS",
                    "number": number,
                    "type": "PR" if is_pr else "ISSUE",
                    "title": data.get("title", ""),
                    "body_summary": body_summary,
                    "labels": labels,
                    "state": data.get("state", "closed"),
                    "url": data.get("html_url", "")
                }
                _cache[cache_key] = result
                return result

    except urllib.error.HTTPError as e:
        if e.code == 404:
            result = {"status": "NOT_FOUND", "number": number, "type": "UNKNOWN", "title": "", "body_summary": "", "labels": [], "state": None, "url": None}
        elif e.code == 403:
            result = {"status": "RATE_LIMIT", "number": number, "type": "UNKNOWN", "title": "", "body_summary": "", "labels": [], "state": None, "url": None}
        else:
            result = {"status": f"HTTP_ERROR_{e.code}", "number": number, "type": "UNKNOWN", "title": "", "body_summary": "", "labels": [], "state": None, "url": None}
        _cache[cache_key] = result
        return result

    except (urllib.error.URLError, TimeoutError):
        return {"status": "NETWORK_ERROR", "number": number, "type": "UNKNOWN", "title": "", "body_summary": "", "labels": [], "state": None, "url": None}
    except Exception:
        return {"status": "UNKNOWN_ERROR", "number": number, "type": "UNKNOWN", "title": "", "body_summary": "", "labels": [], "state": None, "url": None}

# 하위 호환성을 위한 별칭
fetch_reference = fetch_ref_info
fetch_title = lambda owner, repo, num: fetch_ref_info(owner, repo, num).get("title", "")