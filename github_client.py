import urllib.request
import urllib.error
import json
import os

_cache = {}

def fetch_ref_info(owner, repo, number):
    cache_key = f"{owner}/{repo}#{number}"
    if cache_key in _cache:
        return _cache[cache_key]

    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Why-Blame-Client"
    }
    
    # [핵심 수정] GITHUB_TOKEN이 있으면 인증 헤더 추가 (Rate Limit 60회 -> 5,000회 확장)
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
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

fetch_reference = fetch_ref_info
fetch_title = lambda owner, repo, num: fetch_ref_info(owner, repo, num).get("title", "")