import unittest
from consistency import check_evidence_consistency


class TestEvidenceConsistency(unittest.TestCase):
    def test_consistent_commit_and_pr(self):
        """핵심 도메인 키워드가 일치하는 정상 케이스 (HIGH)"""
        c = "fix payment cancellation bug"
        p = "Prevent duplicate payment after cancellation"
        res = check_evidence_consistency(c, p)
        self.assertEqual(res["level"], "HIGH")

    def test_inconsistent_commit_and_pr(self):
        """서로 완전히 다른 주제를 다루는 가짜 증거 차단 케이스 (INCONSISTENT)"""
        c = "fix payment cancellation bug"
        p = "Refactor authentication middleware"
        res = check_evidence_consistency(c, p)
        self.assertEqual(res["level"], "INCONSISTENT")

    def test_unlinked_pr(self):
        """연관 PR이 없는 케이스 (UNLINKED)"""
        c = "fix payment cancellation bug"
        res = check_evidence_consistency(c, "")
        self.assertEqual(res["level"], "UNLINKED")

    def test_domain_synonym_match(self):
        """단어가 달라도 유의어 클러스터(cache <-> redis)에 의해 일치하는 케이스 (HIGH)"""
        c = "fix cache issue"
        p = "Improve Redis connection handling"
        res = check_evidence_consistency(c, p)
        self.assertEqual(res["level"], "HIGH")

    def test_accidental_single_word_overlap(self):
        """단어 1개(user)만 우연히 겹쳐 애매한 경우 HIGH를 주지 않고 MODERATE로 판정"""
        c = "fix user payment bug"
        p = "update user profile page"
        res = check_evidence_consistency(c, p)
        self.assertEqual(res["level"], "MODERATE")


if __name__ == "__main__":
    unittest.main()