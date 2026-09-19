import urllib.request
import urllib.error
import json
import os

CACHE_FILE = ".why_blame_cache.json"
_cache = {}

def _load_cache():
    global _cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                _cache = json.load(f)
        except Exception:
            _cache = {}

def _save_cache():
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

_load_cache()

def _make_request(url):
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Why-Blame-Client"
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(url, headers=headers)

def fetch_ref_info(owner, repo, number):
    """이슈 또는 PR 번호 기반 메타데이터 조회 (캐싱 지원)"""
    cache_key = f"{owner}/{repo}#{number}"
    if cache_key in _cache:
        return _cache[cache_key]

    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}"
    req = _make_request(url)
    try:
        with urllib.request.urlopen(req, timeout=3.0) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                is_pr = "pull_request" in data
                
                body = data.get("body") or ""
                summary_lines = [l.strip() for l in body.splitlines() if l.strip() and not l.startswith("#")]
                body_summary = " ".join(summary_lines[:2])[:120] if summary_lines else ""
                labels = [lbl.get("name", "") for lbl in data.get("labels", []) if isinstance(lbl, dict)]

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
                _save_cache()
                return result

    except urllib.error.HTTPError as e:
        status = "NOT_FOUND" if e.code == 404 else ("RATE_LIMIT" if e.code == 403 else f"HTTP_ERROR_{e.code}")
        result = {"status": status, "number": number, "type": "UNKNOWN", "title": "", "body_summary": "", "labels": [], "state": None, "url": None}
        _cache[cache_key] = result
        _save_cache()
        return result
    except Exception:
        return {"status": "NETWORK_ERROR", "number": number, "type": "UNKNOWN", "title": "", "body_summary": "", "labels": [], "state": None, "url": None}

def fetch_commit_prs(owner, repo, commit_sha):
    """
    [핵심 신규 기능] 커밋 SHA를 기반으로 GitHub API를 호출해 실제 머지된 PR을 탐색합니다.
    GET /repos/{owner}/{repo}/commits/{sha}/pulls
    """
    cache_key = f"sha_prs:{owner}/{repo}#{commit_sha}"
    if cache_key in _cache:
        return _cache[cache_key]

    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}/pulls"
    req = _make_request(url)
    try:
        with urllib.request.urlopen(req, timeout=3.0) as response:
            if response.status == 200:
                prs_data = json.loads(response.read().decode("utf-8"))
                results = []
                for p in prs_data:
                    body = p.get("body") or ""
                    summary_lines = [l.strip() for l in body.splitlines() if l.strip() and not l.startswith("#")]
                    body_summary = " ".join(summary_lines[:2])[:120] if summary_lines else ""
                    labels = [lbl.get("name", "") for lbl in p.get("labels", []) if isinstance(lbl, dict)]
                    results.append({
                        "status": "SUCCESS",
                        "number": p.get("number"),
                        "type": "PR",
                        "title": p.get("title", ""),
                        "body_summary": body_summary,
                        "labels": labels,
                        "state": p.get("state", "closed"),
                        "url": p.get("html_url", "")
                    })
                _cache[cache_key] = results
                _save_cache()
                return results
    except Exception:
        return []

fetch_reference = fetch_ref_info
fetch_title = lambda owner, repo, num: fetch_ref_info(owner, repo, num).get("title", "")