import unittest
from unittest.mock import patch, MagicMock
import urllib.error
import json
import github_client


class TestGitHubClient(unittest.TestCase):
    def setUp(self):
        # 매 테스트마다 캐시 초기화
        github_client._cache.clear()

    @patch("urllib.request.urlopen")
    def test_fetch_pr_detection(self, mock_urlopen):
        """pull_request 키가 있을 때 PR 타입으로 정확히 식별하는지 검증"""
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({
            "title": "Fix duplicate payment bug",
            "state": "closed",
            "html_url": "https://github.com/test/repo/pull/205",
            "pull_request": {"url": "https://api.github.com/..."}
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        res = github_client.fetch_ref_info("test", "repo", 205)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["type"], "PR")
        self.assertEqual(res["title"], "Fix duplicate payment bug")
        self.assertEqual(res["url"], "https://github.com/test/repo/pull/205")

    @patch("urllib.request.urlopen")
    def test_fetch_issue_detection(self, mock_urlopen):
        """pull_request 키가 없을 때 ISSUE 타입으로 식별하는지 검증"""
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({
            "title": "Payment gateway timeout issue",
            "state": "open",
            "html_url": "https://github.com/test/repo/issues/100"
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        res = github_client.fetch_ref_info("test", "repo", 100)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["type"], "ISSUE")
        self.assertEqual(res["title"], "Payment gateway timeout issue")

    @patch("urllib.request.urlopen")
    def test_http_404_not_found(self, mock_urlopen):
        """존재하지 않는 이슈 조회 시 NOT_FOUND 상태 반환 검증"""
        mock_urlopen.side_effect = urllib.error.HTTPError("url", 404, "Not Found", {}, None)
        res = github_client.fetch_ref_info("test", "repo", 9999)
        self.assertEqual(res["status"], "NOT_FOUND")

    @patch("urllib.request.urlopen")
    def test_http_403_rate_limit(self, mock_urlopen):
        """GitHub API 요청 제한(Rate Limit) 발생 시 RATE_LIMIT 상태 반환 검증"""
        mock_urlopen.side_effect = urllib.error.HTTPError("url", 403, "Rate Limit Exceeded", {}, None)
        res = github_client.fetch_ref_info("test", "repo", 50)
        self.assertEqual(res["status"], "RATE_LIMIT")

    @patch("urllib.request.urlopen")
    def test_caching_mechanism(self, mock_urlopen):
        """동일한 번호 재조회 시 네트워크 요청 없이 캐시에서 반환하는지 검증"""
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({"title": "Cached PR", "pull_request": {}}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        # 첫 번째 호출: urlopen 실행됨
        github_client.fetch_ref_info("test", "repo", 1)
        self.assertEqual(mock_urlopen.call_count, 1)

        # 두 번째 호출: 캐시 적중 -> urlopen 추가 실행 없음
        res2 = github_client.fetch_ref_info("test", "repo", 1)
        self.assertEqual(mock_urlopen.call_count, 1)
        self.assertEqual(res2["title"], "Cached PR")


if __name__ == "__main__":
    unittest.main()