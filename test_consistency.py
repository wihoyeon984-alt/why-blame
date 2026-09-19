import unittest
from consistency import check_evidence_consistency


class TestEvidenceConsistency(unittest.TestCase):
    def test_consistent_commit_and_pr(self):
        """커밋과 PR의 핵심 도메인 키워드가 일치하는 정상 케이스 (HIGH)"""
        c = "fix payment cancellation bug"
        p = "Prevent duplicate payment after cancellation"
        res = check_evidence_consistency(c, p)
        self.assertEqual(res["level"], "HIGH")
        self.assertEqual(res["score"], 1.0)

    def test_inconsistent_commit_and_pr(self):
        """커밋(payment)과 PR(auth)이 완전히 상충되는 가짜 증거 차단 케이스 (INCONSISTENT)"""
        c = "fix payment cancellation bug"
        p = "Refactor authentication middleware"
        res = check_evidence_consistency(c, p)
        self.assertEqual(res["level"], "INCONSISTENT")
        self.assertEqual(res["score"], 0.0)

    def test_unlinked_pr(self):
        """연관 PR이 없는 일반 커밋 케이스 (UNLINKED)"""
        c = "fix payment cancellation bug"
        res = check_evidence_consistency(c, "")
        self.assertEqual(res["level"], "UNLINKED")

    def test_sparse_commit_message(self):
        """커밋 메시지가 극히 짧거나 불용어뿐인 경우 (MODERATE)"""
        c = "fix bug"
        p = "Add user profile validation"
        res = check_evidence_consistency(c, p)
        self.assertEqual(res["level"], "MODERATE")

    def test_partial_domain_match_with_body(self):
        """제목에는 없지만 PR 본문(body)에 도메인 맥락이 존재하는 경우 (HIGH)"""
        c = "handle timeout error"
        p_title = "Improve network resilience"
        p_body = "This fixes gateway timeout issues under heavy load."
        res = check_evidence_consistency(c, p_title, p_body)
        self.assertEqual(res["level"], "HIGH")


if __name__ == "__main__":
    unittest.main()