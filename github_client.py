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


def _empty_ref_result(number, status="NOT_FOUND"):
    return {
        "status": status,
        "number": number,
        "type": "UNKNOWN",
        "title": "",
        "body_summary": "",
        "labels": [],
        "state": None,
        "url": None
    }


def fetch_ref_info(owner, repo, number):
    """
    커밋 메시지의 #번호를 GitHub Issue/PR로 조회한다.

    중요:
    - SUCCESS만 캐시한다.
    - NOT_FOUND / RATE_LIMIT / NETWORK_ERROR 등은 캐시하지 않는다.
      그래야 일시적인 실패가 영구적으로 남지 않는다.
    """

    cache_key = f"{owner}/{repo}#{number}"

    if cache_key in _cache:
        return _cache[cache_key]

    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}"
    req = _make_request(url)

    try:
        with urllib.request.urlopen(req, timeout=3.0) as response:
            if response.status == 200:
                data = json.loads(
                    response.read().decode("utf-8")
                )

                is_pr = "pull_request" in data

                body = data.get("body") or ""
                summary_lines = [
                    line.strip()
                    for line in body.splitlines()
                    if line.strip() and not line.startswith("#")
                ]

                body_summary = (
                    " ".join(summary_lines[:2])[:120]
                    if summary_lines
                    else ""
                )

                labels = [
                    label.get("name", "")
                    for label in data.get("labels", [])
                    if isinstance(label, dict)
                ]

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
        if e.code == 404:
            return _empty_ref_result(number, "NOT_FOUND")

        if e.code == 403:
            return _empty_ref_result(number, "RATE_LIMIT")

        return _empty_ref_result(number, f"HTTP_ERROR_{e.code}")

    except Exception:
        return _empty_ref_result(number, "NETWORK_ERROR")

    return _empty_ref_result(number, "UNKNOWN")


def fetch_commit_prs(owner, repo, commit_sha):
    """
    커밋 SHA를 기반으로 실제 연결된 GitHub PR을 탐색한다.

    GET:
    /repos/{owner}/{repo}/commits/{sha}/pulls

    빈 배열이나 네트워크 오류는 캐시하지 않는다.
    """

    cache_key = f"sha_prs:{owner}/{repo}#{commit_sha}"

    if cache_key in _cache:
        return _cache[cache_key]

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/commits/{commit_sha}/pulls"
    )

    req = _make_request(url)

    try:
        with urllib.request.urlopen(req, timeout=3.0) as response:
            if response.status == 200:
                prs_data = json.loads(
                    response.read().decode("utf-8")
                )

                results = []

                for pr in prs_data:
                    body = pr.get("body") or ""

                    summary_lines = [
                        line.strip()
                        for line in body.splitlines()
                        if line.strip() and not line.startswith("#")
                    ]

                    body_summary = (
                        " ".join(summary_lines[:2])[:120]
                        if summary_lines
                        else ""
                    )

                    labels = [
                        label.get("name", "")
                        for label in pr.get("labels", [])
                        if isinstance(label, dict)
                    ]

                    results.append({
                        "status": "SUCCESS",
                        "number": pr.get("number"),
                        "type": "PR",
                        "title": pr.get("title", ""),
                        "body_summary": body_summary,
                        "labels": labels,
                        "state": pr.get("state", "closed"),
                        "url": pr.get("html_url", "")
                    })

                # 실제 PR이 발견된 경우만 캐시
                if results:
                    _cache[cache_key] = results
                    _save_cache()

                return results

    except urllib.error.HTTPError:
        return []

    except Exception:
        return []

    return []


fetch_reference = fetch_ref_info

fetch_title = lambda owner, repo, num: (
    fetch_ref_info(owner, repo, num).get("title", "")
)