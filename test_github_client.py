import unittest
from unittest.mock import patch, MagicMock
import urllib.error
import json
import github_client


class TestGitHubClient(unittest.TestCase):
    def setUp(self):
        github_client._cache.clear()

    @patch("urllib.request.urlopen")
    def test_fetch_pr_with_body_and_labels(self, mock_urlopen):
        """PR 감지, 본문 요약문(body_summary) 및 라벨 추출 검증"""
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({
            "title": "Fix duplicate payment bug",
            "body": "## Summary\nUsers clicked payment button twice.\nPrevent duplicate execution.",
            "labels": [{"name": "bug"}, {"name": "billing"}],
            "state": "closed",
            "html_url": "https://github.com/test/repo/pull/205",
            "pull_request": {"url": "https://api.github.com/..."}
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        res = github_client.fetch_ref_info("test", "repo", 205)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["type"], "PR")
        self.assertEqual(res["title"], "Fix duplicate payment bug")
        self.assertEqual(res["body_summary"], "Users clicked payment button twice. Prevent duplicate execution.")
        self.assertEqual(res["labels"], ["bug", "billing"])
        self.assertEqual(res["url"], "https://github.com/test/repo/pull/205")

    @patch("urllib.request.urlopen")
    def test_fetch_issue_detection(self, mock_urlopen):
        """일반 Issue 식별 검증"""
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({
            "title": "Payment timeout issue",
            "body": "Timeout happens on network glitch.",
            "labels": [],
            "state": "open",
            "html_url": "https://github.com/test/repo/issues/100"
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        res = github_client.fetch_ref_info("test", "repo", 100)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["type"], "ISSUE")
        self.assertEqual(res["title"], "Payment timeout issue")

    @patch("urllib.request.urlopen")
    def test_http_404_not_found(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError("url", 404, "Not Found", {}, None)
        res = github_client.fetch_ref_info("test", "repo", 9999)
        self.assertEqual(res["status"], "NOT_FOUND")

    @patch("urllib.request.urlopen")
    def test_http_403_rate_limit(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError("url", 403, "Rate Limit Exceeded", {}, None)
        res = github_client.fetch_ref_info("test", "repo", 50)
        self.assertEqual(res["status"], "RATE_LIMIT")

    @patch("urllib.request.urlopen")
    def test_caching_mechanism(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({"title": "Cached PR", "pull_request": {}}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        github_client.fetch_ref_info("test", "repo", 1)
        self.assertEqual(mock_urlopen.call_count, 1)

        res2 = github_client.fetch_ref_info("test", "repo", 1)
        self.assertEqual(mock_urlopen.call_count, 1)
        self.assertEqual(res2["title"], "Cached PR")


if __name__ == "__main__":
    unittest.main()