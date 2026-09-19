import unittest
from unittest.mock import patch, MagicMock

from git_tracker import extract_git_history


class TestGitTracker(unittest.TestCase):

    @patch("git_tracker.subprocess.run")
    def test_extracts_added_and_deleted_diff(self, mock_run):
        """?ㅼ젣 extract_git_history()媛 + / - Diff瑜?紐⑤몢 異붿텧?섎뒗吏 ?뺤씤"""

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

        result = extract_git_history("service.py", 2, 2)

        self.assertEqual(len(result), 1)

        commit = result[0]

        self.assertEqual(
            commit["diff_lines"][0],
            "- if user.is_active:"
        )

        self.assertEqual(
            commit["diff_lines"][1],
            "+ if user.is_active and not user.is_duplicate:"
        )

    @patch("git_tracker.subprocess.run")
    def test_diff_reference_is_not_treated_as_issue(self, mock_run):
        """
        Diff ?덉쓽 '#999'??Issue/PR 踰덊샇濡?異붿텧?섎㈃ ???⑸땲??
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

        result = extract_git_history("service.py", 2, 2)

        self.assertEqual(len(result), 1)

        commit = result[0]

        self.assertEqual(commit["refs"], [])

    @patch("git_tracker.subprocess.run")
    def test_commit_message_reference_is_extracted(self, mock_run):
        """Commit message??#123? ?뺤긽?곸쑝濡?異붿텧?섏뼱???⑸땲??"""

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

        result = extract_git_history("service.py", 2, 2)

        self.assertEqual(len(result), 1)

        commit = result[0]

        self.assertEqual(commit["refs"], ["123"])

    @patch("git_tracker.subprocess.run")
    def test_revert_is_detected_from_commit_message(self, mock_run):
        """Revert ?щ???commit message?먯꽌留??먮떒?⑸땲??"""

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

        result = extract_git_history("service.py", 2, 2)

        self.assertEqual(len(result), 1)

        commit = result[0]

        self.assertTrue(commit["is_revert"])

    @patch("git_tracker.subprocess.run")
    def test_korean_commit_message(self, mock_run):
        """UTF-8 ?쒓? commit message媛 源⑥?吏 ?딅뒗吏 ?뺤씤?⑸땲??"""

        sample_log = """commit abc1234
Author: test
Date: 2026-09-18

    寃곗젣 寃利?濡쒖쭅 ?섏젙

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

        result = extract_git_history("service.py", 2, 2)

        self.assertEqual(len(result), 1)

        self.assertEqual(
            result[0]["message"],
            "寃곗젣 寃利?濡쒖쭅 ?섏젙"
        )



    @patch("git_tracker.subprocess.run")
    def test_revert_word_in_normal_commit_is_not_revert(self, mock_run):
        """일반 커밋 메시지의 revert라는 단어를 실제 Revert로 오판하면 안 됩니다."""

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

        result = extract_git_history("service.py", 2, 2)

        self.assertEqual(len(result), 1)
        self.assertFalse(result[0]["is_revert"])

if __name__ == "__main__":
    unittest.main()
