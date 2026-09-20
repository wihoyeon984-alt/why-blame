import unittest
from unittest.mock import MagicMock, patch

from git_tracker import extract_git_history


class TestGitTracker(unittest.TestCase):

    @patch("git_tracker.subprocess.run")
    def test_extracts_added_and_deleted_diff(self, mock_run):
        """extract_git_history()가 추가/삭제 Diff를 모두 추출하는지 확인합니다."""

        sample_log = """commit 2c17f74
Author: test
Date: 2026-09-18

    fix: prevent duplicate charge

diff --git a/service.py b/service.py
--- a/service.py
+++ b/service.py
@@ -2,1 +2,1 @@
-   if user.is_active:
+   if user.is_active and not user.is_duplicate:
"""

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = sample_log
        mock_result.stderr = ""

        mock_run.return_value = mock_result

        result = extract_git_history(
            "service.py",
            2,
            2,
        )

        self.assertEqual(len(result), 1)

        commit = result[0]

        self.assertEqual(
            commit["diff_lines"][0],
            "- if user.is_active:",
        )

        self.assertEqual(
            commit["diff_lines"][1],
            "+ if user.is_active and not user.is_duplicate:",
        )

    @patch("git_tracker.subprocess.run")
    def test_diff_reference_is_not_treated_as_issue(self, mock_run):
        """
        Diff 내부의 '#999'를 Issue/PR 번호로 추출하면 안 됩니다.
        """

        sample_log = """commit abc1234
Author: test
Date: 2026-09-18

    fix: improve validation

diff --git a/service.py b/service.py
--- a/service.py
+++ b/service.py
@@ -2,1 +2,2 @@
+   # related to issue #999
+   if user.is_active:
"""

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = sample_log
        mock_result.stderr = ""

        mock_run.return_value = mock_result

        result = extract_git_history(
            "service.py",
            2,
            2,
        )

        self.assertEqual(len(result), 1)

        commit = result[0]

        self.assertEqual(
            commit["refs"],
            [],
        )

    @patch("git_tracker.subprocess.run")
    def test_commit_message_reference_is_extracted(self, mock_run):
        """
        Commit message의 #123이 정상적으로 참조 번호로 추출되는지 확인합니다.
        """

        sample_log = """commit abc1234
Author: test
Date: 2026-09-18

    fix: prevent duplicate payment #123

diff --git a/service.py b/service.py
--- a/service.py
+++ b/service.py
@@ -2,1 +2,1 @@
-   charge(user)
+   charge_once(user)
"""

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = sample_log
        mock_result.stderr = ""

        mock_run.return_value = mock_result

        result = extract_git_history(
            "service.py",
            2,
            2,
        )

        self.assertEqual(len(result), 1)

        commit = result[0]

        self.assertEqual(
            commit["refs"],
            ["123"],
        )

    @patch("git_tracker.subprocess.run")
    def test_revert_is_detected_from_commit_message(self, mock_run):
        """
        Revert 여부를 Commit message의 시작 부분에서 판단하는지 확인합니다.
        """

        sample_log = """commit abc1234
Author: test
Date: 2026-09-18

    Revert "fix: payment validation"

diff --git a/service.py b/service.py
--- a/service.py
+++ b/service.py
@@ -2,1 +2,1 @@
-   charge_once(user)
+   charge(user)
"""

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = sample_log
        mock_result.stderr = ""

        mock_run.return_value = mock_result

        result = extract_git_history(
            "service.py",
            2,
            2,
        )

        self.assertEqual(len(result), 1)

        commit = result[0]

        self.assertTrue(
            commit["is_revert"]
        )

    @patch("git_tracker.subprocess.run")
    def test_korean_commit_message(self, mock_run):
        """
        UTF-8 한국어 Commit message가 깨지지 않는지 확인합니다.
        """

        sample_log = """commit abc1234
Author: test
Date: 2026-09-18

    결제 검증 로직 수정

diff --git a/service.py b/service.py
--- a/service.py
+++ b/service.py
@@ -2,1 +2,1 @@
-   charge(user)
+   validate_and_charge(user)
"""

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = sample_log
        mock_result.stderr = ""

        mock_run.return_value = mock_result

        result = extract_git_history(
            "service.py",
            2,
            2,
        )

        self.assertEqual(len(result), 1)

        self.assertEqual(
            result[0]["message"],
            "결제 검증 로직 수정",
        )

    @patch("git_tracker.subprocess.run")
    def test_revert_word_in_normal_commit_is_not_revert(self, mock_run):
        """
        일반 Commit message에 revert라는 단어가 있다는 이유만으로
        실제 Revert Commit으로 오판하면 안 됩니다.
        """

        sample_log = """commit abc1234
Author: test
Date: 2026-09-18

    fix: improve revert handling

diff --git a/service.py b/service.py
--- a/service.py
+++ b/service.py
@@ -2,1 +2,1 @@
-   charge(user)
+   safe_charge(user)
"""

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = sample_log
        mock_result.stderr = ""

        mock_run.return_value = mock_result

        result = extract_git_history(
            "service.py",
            2,
            2,
        )

        self.assertEqual(len(result), 1)

        self.assertFalse(
            result[0]["is_revert"]
        )


if __name__ == "__main__":
    unittest.main()