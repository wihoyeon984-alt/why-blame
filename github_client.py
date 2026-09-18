import urllib.request
import json

def fetch_title(owner, repo, number):
    """GitHub API에서 PR/이슈의 실제 제목을 가져옵니다."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}"
    req = urllib.request.Request(url, headers={"User-Agent": "Why-Blame-App"})
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("title", "")
    except Exception:
        return ""