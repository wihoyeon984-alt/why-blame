import json
import os
import urllib.error
import urllib.request


CACHE_FILE = ".why_blame_cache.json"
_cache = {}


def _load_cache():
    global _cache

    if not os.path.exists(CACHE_FILE):
        _cache = {}
        return

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        _cache = data if isinstance(data, dict) else {}

    except (OSError, json.JSONDecodeError):
        _cache = {}


def _save_cache():
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as file:
            json.dump(
                _cache,
                file,
                ensure_ascii=False,
                indent=2,
            )

    except OSError:
        # 캐시 저장 실패가 Evidence 수집 전체를 중단시키면 안 된다.
        pass


_load_cache()


def _make_request(url):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Why-Blame-Client",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    token = os.getenv("GITHUB_TOKEN")

    if token:
        headers["Authorization"] = f"Bearer {token}"

    return urllib.request.Request(
        url,
        headers=headers,
    )


def _empty_ref_result(
    number,
    status="NOT_FOUND",
    error_message="",
):
    return {
        "status": status,
        "number": number,
        "type": "UNKNOWN",
        "title": "",
        "body_summary": "",
        "labels": [],
        "state": None,
        "url": None,
        "error_message": error_message,
    }


def _read_http_error_body(error):
    """
    GitHub HTTP 오류 응답의 body를 안전하게 읽는다.
    """
    try:
        raw = error.read()

        if not raw:
            return ""

        return raw.decode(
            "utf-8",
            errors="replace",
        )

    except Exception:
        return ""


def _extract_error_message(body):
    """
    GitHub JSON 오류 응답에서 message를 추출한다.
    """
    if not body:
        return ""

    try:
        data = json.loads(body)

        if isinstance(data, dict):
            return str(data.get("message", ""))

    except (json.JSONDecodeError, TypeError):
        pass

    return ""


def _header_value(headers, name):
    """
    HTTP header 값을 안전하게 가져온다.
    """
    if headers is None:
        return None

    try:
        return headers.get(name)

    except Exception:
        return None


def _classify_http_error(error):
    """
    GitHub HTTP 오류를 확인 가능한 Evidence를 기준으로 분류한다.

    중요한 원칙:
    403이라는 이유만으로 RATE_LIMIT이라고 단정하지 않는다.

    반환:
        (status, message)
    """
    code = getattr(error, "code", None)

    body = _read_http_error_body(error)
    message = _extract_error_message(body)

    headers = getattr(error, "headers", None)

    remaining = _header_value(
        headers,
        "X-RateLimit-Remaining",
    )

    retry_after = _header_value(
        headers,
        "Retry-After",
    )

    message_lower = message.lower()

    if code == 404:
        return "NOT_FOUND", message

    if code == 401:
        return "UNAUTHORIZED", message

    if code == 403:
        # Primary rate limit의 직접적인 근거
        if str(remaining).strip() == "0":
            return "RATE_LIMIT", message

        # Secondary rate limit에서 Retry-After가 제공된 경우
        if retry_after:
            return "RATE_LIMIT", message

        # GitHub 응답 message가 rate limit을 명시하는 경우
        if (
            "rate limit" in message_lower
            or "secondary rate" in message_lower
            or "abuse detection" in message_lower
        ):
            return "RATE_LIMIT", message

        # 403은 확인했지만 rate limit이라는 증거는 없다.
        return "FORBIDDEN", message

    if code == 429:
        return "RATE_LIMIT", message

    if code is not None:
        return f"HTTP_ERROR_{code}", message

    return "HTTP_ERROR", message


def _summarize_body(body, max_length=180):
    """
    GitHub PR/Issue 본문을 Evidence context로 정리한다.

    Markdown heading은 문서 구조이므로 제거하고,
    실제 본문 내용만 보존한다.
    """
    if not body:
        return ""

    cleaned_lines = []

    for line in body.splitlines():
        stripped = line.strip()

        if not stripped:
            continue

        # Markdown heading은 Evidence 내용에서 제외한다.
        if stripped.startswith("#"):
            continue

        cleaned_lines.append(stripped)

    summary = " ".join(cleaned_lines)

    if len(summary) > max_length:
        summary = summary[:max_length - 3] + "..."

    return summary


def _build_ref_result(data, number):
    """
    GitHub Issue API 응답을 why-blame Evidence 구조로 변환한다.
    """
    is_pr = "pull_request" in data
    ref_type = "PR" if is_pr else "ISSUE"

    body = data.get("body") or ""
    body_summary = _summarize_body(body)

    labels = []

    for label in data.get("labels", []):
        if isinstance(label, dict):
            name = label.get("name")

            if name:
                labels.append(name)

    return {
        "status": "SUCCESS",
        "number": number,
        "type": ref_type,
        "title": data.get("title", ""),
        "body_summary": body_summary,
        "labels": labels,
        "state": data.get("state"),
        "url": data.get("html_url", ""),
        "error_message": "",
    }


def fetch_ref_info(owner, repo, number):
    """
    Commit message 등에 포함된 #번호를
    GitHub Issue / PR Evidence로 조회한다.

    캐시 정책:
    - SUCCESS만 캐시한다.
    - 조회 실패는 캐시하지 않는다.

    따라서 일시적인 API 실패를 영구적인
    '증거 없음'으로 오인하지 않는다.
    """
    cache_key = f"{owner}/{repo}#{number}"

    if cache_key in _cache:
        return _cache[cache_key]

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/issues/{number}"
    )

    request = _make_request(url)

    try:
        with urllib.request.urlopen(
            request,
            timeout=3.0,
        ) as response:

            if response.status != 200:
                return _empty_ref_result(
                    number,
                    f"HTTP_ERROR_{response.status}",
                )

            data = json.loads(
                response.read().decode("utf-8")
            )

            result = _build_ref_result(
                data,
                number,
            )

            _cache[cache_key] = result
            _save_cache()

            return result

    except urllib.error.HTTPError as error:
        status, message = _classify_http_error(
            error
        )

        return _empty_ref_result(
            number,
            status,
            message,
        )

    except (
        urllib.error.URLError,
        TimeoutError,
        OSError,
    ) as error:
        return _empty_ref_result(
            number,
            "NETWORK_ERROR",
            str(error),
        )

    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ) as error:
        return _empty_ref_result(
            number,
            "INVALID_RESPONSE",
            str(error),
        )

    except Exception as error:
        return _empty_ref_result(
            number,
            "UNKNOWN_ERROR",
            str(error),
        )


def _build_pr_result(pr):
    """
    GitHub commit -> PR API의 PR 객체를
    Timeline Evidence 구조로 변환한다.
    """
    body = pr.get("body") or ""
    body_summary = _summarize_body(body)

    labels = []

    for label in pr.get("labels", []):
        if isinstance(label, dict):
            name = label.get("name")

            if name:
                labels.append(name)

    return {
        "status": "SUCCESS",
        "number": pr.get("number"),
        "type": "PR",
        "title": pr.get("title", ""),
        "body_summary": body_summary,
        "labels": labels,
        "state": pr.get("state"),
        "url": pr.get("html_url", ""),
        "error_message": "",
    }


def fetch_commit_prs(owner, repo, commit_sha):
    """
    Commit SHA를 기반으로 연결된 GitHub PR 목록을 조회한다.

    기존 interface와의 호환성을 유지한다.

    성공 + PR 존재:
        list 반환
        last_status = SUCCESS

    성공 + PR 없음:
        [] 반환
        last_status = UNLINKED

    조회 실패:
        [] 반환
        last_status에 실패 원인을 저장한다.

    따라서:
        "PR이 실제로 없음"

    과

        "PR 존재 여부를 확인하지 못함"

    을 구분할 수 있다.
    """
    fetch_commit_prs.last_status = "UNKNOWN"
    fetch_commit_prs.last_error = ""

    cache_key = (
        f"sha_prs:{owner}/{repo}#{commit_sha}"
    )

    if cache_key in _cache:
        fetch_commit_prs.last_status = "SUCCESS"
        return _cache[cache_key]

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/commits/"
        f"{commit_sha}/pulls"
    )

    request = _make_request(url)

    try:
        with urllib.request.urlopen(
            request,
            timeout=3.0,
        ) as response:

            if response.status != 200:
                fetch_commit_prs.last_status = (
                    f"HTTP_ERROR_{response.status}"
                )

                return []

            prs_data = json.loads(
                response.read().decode("utf-8")
            )

            if not isinstance(prs_data, list):
                fetch_commit_prs.last_status = (
                    "INVALID_RESPONSE"
                )

                return []

            results = [
                _build_pr_result(pr)
                for pr in prs_data
                if isinstance(pr, dict)
            ]

            if results:
                _cache[cache_key] = results
                _save_cache()

                fetch_commit_prs.last_status = "SUCCESS"

            else:
                # API 조회는 성공했지만 실제 연결 PR이 없음.
                fetch_commit_prs.last_status = "UNLINKED"

            return results

    except urllib.error.HTTPError as error:
        status, message = _classify_http_error(
            error
        )

        fetch_commit_prs.last_status = status
        fetch_commit_prs.last_error = message

        return []

    except (
        urllib.error.URLError,
        TimeoutError,
        OSError,
    ) as error:
        fetch_commit_prs.last_status = "NETWORK_ERROR"
        fetch_commit_prs.last_error = str(error)

        return []

    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ) as error:
        fetch_commit_prs.last_status = "INVALID_RESPONSE"
        fetch_commit_prs.last_error = str(error)

        return []

    except Exception as error:
        fetch_commit_prs.last_status = "UNKNOWN_ERROR"
        fetch_commit_prs.last_error = str(error)

        return []


# 초기 상태
fetch_commit_prs.last_status = "UNKNOWN"
fetch_commit_prs.last_error = ""


# 기존 코드 호환성 유지
fetch_reference = fetch_ref_info


def fetch_title(owner, repo, num):
    return fetch_ref_info(
        owner,
        repo,
        num,
    ).get("title", "")