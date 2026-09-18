import urllib.request
import urllib.error
import json

# GitHub 공식 예제에 실제로 존재하는 Issue/PR 번호(1347번)를 조회해봅니다
url = "https://api.github.com/repos/octocat/Hello-World/issues/1347"
headers = {"User-Agent": "Why-Blame-Study"}

req = urllib.request.Request(url, headers=headers)

try:
    print(f"[*] GitHub API에 연결 요청 중... ({url})")
    response = urllib.request.urlopen(req, timeout=5)
    data = json.loads(response.read().decode("utf-8"))
    
    print("\n=== GitHub API 응답 성공! ===")
    print("번호:", data.get("number"))
    print("제목:", data.get("title"))
    print("작성자:", data.get("user", {}).get("login"))
    print("상태:", data.get("state"))
    print("생성일:", data.get("created_at")[:10])

except urllib.error.HTTPError as e:
    print(f"\n[HTTP 오류 {e.code}] 해당 번호의 PR/이슈를 찾을 수 없거나 권한이 없습니다.")
except Exception as e:
    print(f"\n[네트워크 오류] 연결 실패: {e}")