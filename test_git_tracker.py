import unittest

def parse_diff_lines_from_log(raw_log_lines):
    diff_lines = []
    in_diff = False
    for l in raw_log_lines:
        if l.startswith("diff --git"):
            in_diff = True
            continue
        if in_diff:
            if l.startswith("+") and not l.startswith("+++"):
                diff_lines.append("+ " + l[1:].strip())
            elif l.startswith("-") and not l.startswith("---"):
                diff_lines.append("- " + l[1:].strip())
    return diff_lines

class TestGitTrackerDiff(unittest.TestCase):
    def test_diff_extraction_ignores_headers(self):
        sample_log = [
            "commit 2c17f74",
            "Author: test",
            "Date: 2026-09-18",
            "    fix: prevent duplicate charge",
            "diff --git a/service.py b/service.py",
            "--- a/service.py",
            "+++ b/service.py",
            "@@ -2,1 +2,1 @@",
            "-   if user.is_active:",
            "+   if user.is_active and not user.is_duplicate:"
        ]
        diffs = parse_diff_lines_from_log(sample_log)

        self.assertEqual(len(diffs), 2)
        self.assertEqual(diffs[0], "- if user.is_active:")
        self.assertEqual(diffs[-1], "+ if user.is_active and not user.is_duplicate:")

if __name__ == "__main__":
    unittest.main()
