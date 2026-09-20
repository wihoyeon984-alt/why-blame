import io
import json
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

import github_client


class TestGitHubClient(unittest.TestCase):

    def setUp(self):
        github_client._cache.clear()

    @patch("urllib.request.urlopen")
    def test_fetch_pr_with_body_and_labels(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps(
            {
                "title": "Fix duplicate payment bug",
                "body": (
                    "## Summary\n"
                    "Users clicked payment button twice.\n"
                    "Prevent duplicate execution."
                ),
                "labels": [
                    {"name": "bug"},
                    {"name": "billing"},
                ],
                "state": "closed",
                "html_url": "https://github.com/test/repo/pull/205",
                "pull_request": {
                    "url": "https://api.github.com/test/repo/pulls/205"
                },
            }
        ).encode("utf-8")

        mock_urlopen.return_value.__enter__.return_value = mock_resp

        res = github_client.fetch_ref_info(
            "test",
            "repo",
            205,
        )

        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["type"], "PR")
        self.assertEqual(
            res["title"],
            "Fix duplicate payment bug",
        )
        self.assertEqual(
            res["body_summary"],
            (
                "Users clicked payment button twice. "
                "Prevent duplicate execution."
            ),
        )
        self.assertEqual(
            res["labels"],
            ["bug", "billing"],
        )

    @patch("urllib.request.urlopen")
    def test_fetch_commit_prs_by_sha(self, mock_urlopen):
        """커밋 SHA로 실제 연결된 PR 목록을 가져오는지 검증한다."""
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps(
            [
                {
                    "number": 300,
                    "title": "PR from Commit SHA",
                    "body": "Linked PR description",
                    "labels": [
                        {"name": "feature"}
                    ],
                    "state": "closed",
                    "html_url": "https://github.com/test/repo/pull/300",
                }
            ]
        ).encode("utf-8")

        mock_urlopen.return_value.__enter__.return_value = mock_resp

        prs = github_client.fetch_commit_prs(
            "test",
            "repo",
            "a1b2c3d",
        )

        self.assertEqual(len(prs), 1)
        self.assertEqual(prs[0]["number"], 300)
        self.assertEqual(
            prs[0]["title"],
            "PR from Commit SHA",
        )
        self.assertEqual(prs[0]["type"], "PR")

        self.assertEqual(
            github_client.fetch_commit_prs.last_status,
            "SUCCESS",
        )

    @patch("urllib.request.urlopen")
    def test_http_404_not_found(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "url",
            404,
            "Not Found",
            {},
            None,
        )

        res = github_client.fetch_ref_info(
            "test",
            "repo",
            9999,
        )

        self.assertEqual(
            res["status"],
            "NOT_FOUND",
        )

    @patch("urllib.request.urlopen")
    def test_caching_mechanism(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps(
            {
                "title": "Cached PR",
                "pull_request": {},
            }
        ).encode("utf-8")

        mock_urlopen.return_value.__enter__.return_value = mock_resp

        github_client.fetch_ref_info(
            "test",
            "repo",
            1,
        )

        self.assertEqual(
            mock_urlopen.call_count,
            1,
        )

        res2 = github_client.fetch_ref_info(
            "test",
            "repo",
            1,
        )

        self.assertEqual(
            mock_urlopen.call_count,
            1,
        )
        self.assertEqual(
            res2["title"],
            "Cached PR",
        )

    def test_403_without_rate_limit_evidence_is_forbidden(self):
        """
        403만으로 RATE_LIMIT이라고 단정하지 않는다.
        Rate-limit 근거가 없다면 FORBIDDEN으로 분류한다.
        """
        error = urllib.error.HTTPError(
            url="https://api.github.com/test",
            code=403,
            msg="Forbidden",
            hdrs={
                "X-RateLimit-Remaining": "42",
            },
            fp=io.BytesIO(
                b'{"message": "Forbidden"}'
            ),
        )

        status, message = github_client._classify_http_error(error)

        self.assertEqual(status, "FORBIDDEN")
        self.assertEqual(message, "Forbidden")

    def test_403_with_remaining_zero_is_rate_limit(self):
        """
        403과 함께 X-RateLimit-Remaining이 0이면
        RATE_LIMIT으로 분류한다.
        """
        error = urllib.error.HTTPError(
            url="https://api.github.com/test",
            code=403,
            msg="Forbidden",
            hdrs={
                "X-RateLimit-Remaining": "0",
            },
            fp=io.BytesIO(
                b'{"message": "API rate limit exceeded"}'
            ),
        )

        status, message = github_client._classify_http_error(error)

        self.assertEqual(status, "RATE_LIMIT")
        self.assertIn(
            "rate limit",
            message.lower(),
        )

    def test_429_is_rate_limit(self):
        """HTTP 429는 RATE_LIMIT으로 분류한다."""
        error = urllib.error.HTTPError(
            url="https://api.github.com/test",
            code=429,
            msg="Too Many Requests",
            hdrs={
                "Retry-After": "60",
            },
            fp=io.BytesIO(
                b'{"message": "Too many requests"}'
            ),
        )

        status, message = github_client._classify_http_error(error)

        self.assertEqual(status, "RATE_LIMIT")
        self.assertEqual(
            message,
            "Too many requests",
        )

    @patch("github_client.urllib.request.urlopen")
    def test_network_error_is_not_treated_as_unlinked(
        self,
        mock_urlopen,
    ):
        """
        네트워크 실패와 실제 PR 없음은 서로 다른 상태여야 한다.
        """
        mock_urlopen.side_effect = urllib.error.URLError(
            "temporary network failure"
        )

        result = github_client.fetch_commit_prs(
            "owner",
            "repo",
            "deadbeef1234567890",
        )

        self.assertEqual(result, [])

        self.assertEqual(
            github_client.fetch_commit_prs.last_status,
            "NETWORK_ERROR",
        )

        self.assertNotEqual(
            github_client.fetch_commit_prs.last_status,
            "UNLINKED",
        )

        self.assertIn(
            "temporary network failure",
            github_client.fetch_commit_prs.last_error,
        )


if __name__ == "__main__":
    unittest.main()