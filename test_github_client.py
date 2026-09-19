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

    @patch("urllib.request.urlopen")
    def test_fetch_commit_prs_by_sha(self, mock_urlopen):
        """커밋 해시(SHA)로 실제 연결된 PR 목록을 가져오는지 검증"""
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps([{
            "number": 300,
            "title": "PR from Commit SHA",
            "body": "Linked PR description",
            "labels": [{"name": "feature"}],
            "state": "closed",
            "html_url": "https://github.com/test/repo/pull/300"
        }]).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        prs = github_client.fetch_commit_prs("test", "repo", "a1b2c3d")
        self.assertEqual(len(prs), 1)
        self.assertEqual(prs[0]["number"], 300)
        self.assertEqual(prs[0]["title"], "PR from Commit SHA")
        self.assertEqual(prs[0]["type"], "PR")

    @patch("urllib.request.urlopen")
    def test_http_404_not_found(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError("url", 404, "Not Found", {}, None)
        res = github_client.fetch_ref_info("test", "repo", 9999)
        self.assertEqual(res["status"], "NOT_FOUND")

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