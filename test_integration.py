import os
import subprocess
import tempfile
import unittest

from git_tracker import extract_git_history
from narrative import synthesize_narrative
from timeline import build_timeline


class TestWhyBlameIntegration(unittest.TestCase):

    def setUp(self):
        """
        각 테스트마다 독립적인 실제 Git Repository를 생성한다.

        개발 중인 why-blame Repository와 사용자의 전역 Git 설정에는
        영향을 주지 않는다.
        """
        self.original_cwd = os.getcwd()
        self.temp_dir = tempfile.TemporaryDirectory()

        os.chdir(self.temp_dir.name)

        self.run_git("init")
        self.run_git(
            "config",
            "user.name",
            "Why Blame Test",
        )
        self.run_git(
            "config",
            "user.email",
            "why-blame@example.test",
        )

    def tearDown(self):
        os.chdir(self.original_cwd)
        self.temp_dir.cleanup()

    def run_git(self, *args):
        """임시 Repository에서 실제 Git 명령을 실행한다."""
        result = subprocess.run(
            ["git"] + list(args),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0:
            self.fail(
                "Git command failed: "
                + "git "
                + " ".join(args)
                + "\n"
                + result.stderr
            )

        return result.stdout.strip()

    def write_service(self, condition):
        """Integration Test에서 사용할 service.py를 생성한다."""
        content = (
            "def pay(user):\n"
            "    if " + condition + ":\n"
            "        charge(user)\n"
        )

        with open(
            "service.py",
            "w",
            encoding="utf-8",
            newline="\n",
        ) as file:
            file.write(content)

    def commit_service(self, message):
        """현재 service.py 변경을 실제 Git Commit으로 저장한다."""
        self.run_git(
            "add",
            "service.py",
        )

        self.run_git(
            "commit",
            "-m",
            message,
        )

    def create_history(self):
        """
        실제 Git Repository에 3단계 변경 이력을 생성한다.

        1. 최초 payment flow
        2. duplicate charge 방지
        3. cancelled order 처리
        """
        self.write_service(
            "user.is_active"
        )

        self.commit_service(
            "feat: initial payment flow"
        )

        self.write_service(
            "user.is_active "
            "and not user.is_duplicate"
        )

        self.commit_service(
            "fix: prevent duplicate charge"
        )

        self.write_service(
            "user.is_active "
            "and not user.is_duplicate "
            "and not user.is_cancelled"
        )

        self.commit_service(
            "fix: handle cancelled orders"
        )

    def extract_history(self):
        """
        실제 git log -L을 통해 service.py 변경 이력을 추출한다.
        """
        return extract_git_history(
            "service.py",
            1,
            3,
        )

    @staticmethod
    def no_reference(owner, repo, number):
        """
        Commit Message Reference 조회 결과가 없다는
        deterministic GitHub Evidence 응답을 제공한다.
        """
        return {
            "status": "NOT_FOUND",
            "number": number,
            "type": "UNKNOWN",
            "title": "",
            "body_summary": "",
            "labels": [],
            "state": None,
            "url": None,
        }

    @staticmethod
    def no_commit_prs(owner, repo, sha):
        """Commit SHA에 연결된 PR이 없는 상황을 표현한다."""
        return []

    @staticmethod
    def find_commit_hash(history, message):
        """특정 Commit Message의 실제 SHA를 찾는다."""
        for commit in history:
            if commit.get("message") == message:
                return commit.get("hash")

        return None

    def test_pipeline_without_external_evidence_is_conservative(self):
        """
        실제 Git History는 존재하지만 외부 Evidence가 없는 경우를 검증한다.

        핵심:
        - Git History는 정상적으로 추출되어야 한다.
        - 외부 Reference가 없음을 stats가 반영해야 한다.
        - 존재하지 않는 변경 원인을 Narrative가 생성하면 안 된다.
        """
        self.create_history()

        history = self.extract_history()

        self.assertGreaterEqual(
            len(history),
            1,
        )

        self.assertTrue(
            all(
                commit.get("hash")
                for commit in history
            )
        )

        self.assertTrue(
            any(
                commit.get("diff_lines")
                for commit in history
            )
        )

        timeline, stats = build_timeline(
            history,
            ("integration", "repo"),
            self.no_reference,
            self.no_commit_prs,
        )

        self.assertTrue(
            timeline
        )

        self.assertEqual(
            timeline[0]["type"],
            "🌱 FIRST OBSERVED",
        )

        self.assertFalse(
            stats["has_refs"]
        )

        self.assertIn(
            stats["consistency"],
            ("UNLINKED", "MODERATE"),
        )

        headline, body = synthesize_narrative(
            timeline,
            stats,
        )

        text = (
            headline + " " + body
        ).lower()

        unsupported_claims = [
            "performance",
            "race condition",
            "production incident",
            "customer complaint",
            "security issue",
        ]

        for claim in unsupported_claims:
            self.assertNotIn(
                claim,
                text,
            )

    def test_pipeline_with_consistent_pr_uses_real_confidence(self):
        """
        실제 Git History와 일치하는 PR Evidence를 연결한다.

        테스트에서 Confidence를 강제로 변경하지 않는다.
        build_timeline()이 실제로 계산한 stats를 그대로
        Narrative에 전달한다.

        핵심:
        - PR Evidence가 실제 Timeline에 연결되어야 한다.
        - Consistency 계산 결과가 충돌 상태가 아니어야 한다.
        - 실제 Confidence가 보존되어야 한다.
        - Evidence에 없는 원인을 추가하면 안 된다.
        """
        self.create_history()

        history = self.extract_history()

        target_hash = self.find_commit_hash(
            history,
            "fix: handle cancelled orders",
        )

        self.assertIsNotNone(
            target_hash
        )

        def fetch_commit_prs(
            owner,
            repo,
            sha,
        ):
            if sha != target_hash:
                return []

            return [
                {
                    "status": "SUCCESS",
                    "number": 101,
                    "type": "PR",
                    "title": (
                        "Handle cancelled orders"
                    ),
                    "body_summary": (
                        "Handle cancelled orders "
                        "in payment flow."
                    ),
                    "labels": ["bug"],
                    "state": "closed",
                    "url": (
                        "https://github.com/"
                        "integration/repo/pull/101"
                    ),
                }
            ]

        timeline, stats = build_timeline(
            history,
            ("integration", "repo"),
            self.no_reference,
            fetch_commit_prs,
        )

        self.assertTrue(
            stats["has_refs"]
        )

        self.assertNotEqual(
            stats["consistency"],
            "INCONSISTENT",
        )

        self.assertFalse(
            stats["is_blocked"]
        )

        self.assertIn(
            stats["confidence"],
            (
                "VERY HIGH",
                "HIGH",
                "MEDIUM",
                "MODERATE",
                "WEAK",
            ),
        )

        linked_prs = [
            ref
            for item in timeline
            for ref in item.get(
                "ref_items",
                [],
            )
            if ref.get("type") == "PR"
        ]

        self.assertEqual(
            len(linked_prs),
            1,
        )

        self.assertEqual(
            linked_prs[0]["number"],
            101,
        )

        self.assertEqual(
            linked_prs[0]["title"],
            "Handle cancelled orders",
        )

        headline, body = synthesize_narrative(
            timeline,
            stats,
        )

        text = (
            headline + " " + body
        ).lower()

        # PR에 존재하지 않는 원인을 만들어내면 안 된다.
        self.assertNotIn(
            "improve performance",
            text,
        )

        self.assertNotIn(
            "race condition",
            text,
        )

        self.assertNotIn(
            "security issue",
            text,
        )

    def test_pipeline_with_inconsistent_pr_blocks_why(self):
        """
        실제 Git History와 PR Evidence가 충돌하는 경우를 검증한다.

        Commit:
            fix: handle cancelled orders

        PR:
            Improve image rendering

        기대:
            INCONSISTENT
            is_blocked = True
            충돌한 PR 내용을 WHY로 채택하지 않음
        """
        self.create_history()

        history = self.extract_history()

        target_hash = self.find_commit_hash(
            history,
            "fix: handle cancelled orders",
        )

        self.assertIsNotNone(
            target_hash
        )

        def fetch_commit_prs(
            owner,
            repo,
            sha,
        ):
            if sha != target_hash:
                return []

            return [
                {
                    "status": "SUCCESS",
                    "number": 700,
                    "type": "PR",
                    "title": (
                        "Improve image rendering"
                    ),
                    "body_summary": (
                        "Optimize image rendering "
                        "for gallery thumbnails."
                    ),
                    "labels": ["graphics"],
                    "state": "closed",
                    "url": (
                        "https://github.com/"
                        "integration/repo/pull/700"
                    ),
                }
            ]

        timeline, stats = build_timeline(
            history,
            ("integration", "repo"),
            self.no_reference,
            fetch_commit_prs,
        )

        self.assertTrue(
            stats["has_refs"]
        )

        self.assertEqual(
            stats["consistency"],
            "INCONSISTENT",
        )

        self.assertTrue(
            stats["is_blocked"]
        )

        self.assertTrue(
            stats["inconsistent_pairs"]
        )

        headline, body = synthesize_narrative(
            timeline,
            stats,
        )

        text = (
            headline + " " + body
        )

        # 충돌한 PR의 내용을 변경 이유로 채택하면 안 된다.
        self.assertNotIn(
            "Improve image rendering",
            headline,
        )

        # Blocked 상태에서도 Evidence 밖의 원인을 만들면 안 된다.
        self.assertNotIn(
            "performance",
            text.lower(),
        )

        self.assertNotIn(
            "security issue",
            text.lower(),
        )


if __name__ == "__main__":
    unittest.main()