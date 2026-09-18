import unittest
from timeline import classify_commit, calculate_evidence_strength

class TestWhyBlameTimeline(unittest.TestCase):
    
    # 1. feat 커밋 테스트
    def test_feat_add_login(self):
        self.assertEqual(classify_commit("feat: add login"), "✨ FEATURE")

    # 2. fix 커밋 테스트
    def test_fix_prevent_duplicate(self):
        self.assertEqual(classify_commit("fix: prevent duplicate login"), "🐛 BUG FIX")

    # 3. revert 커밋 테스트
    def test_revert_login(self):
        self.assertEqual(classify_commit("revert: revert login change", True), "↩ REVERT")

    # 4. refactor 커밋 테스트
    def test_refactor_simplify(self):
        self.assertEqual(classify_commit("refactor: simplify login"), "🧹 REFACTOR")

    # 5. [핵심] Conventional Commits 접두어가 본문 단어보다 우선하는지 테스트!
    def test_feat_fix_login_screen(self):
        # 메시지 본문에 'fix'가 들어있어도 접두어가 feat: 이면 FEATURE로 판정해야 함
        self.assertEqual(classify_commit("feat: fix login screen UI"), "✨ FEATURE")

    # 6. 매우 강력한 증거 시나리오 테스트
    def test_evidence_matrix_very_high(self):
        tl = [
            {"message": "feat: add payment", "diff_lines": ["+ code"], "refs": ["101"], "ref_details": ["#101 ('Title')"], "is_revert": False},
            {"message": "revert: rollback", "diff_lines": ["- code"], "refs": [], "ref_details": [], "is_revert": True}
        ]
        stats = calculate_evidence_strength(tl)
        self.assertEqual(stats["grade"], "VERY HIGH (매우 강력한 근거)")
        self.assertGreaterEqual(stats["score"], 9)

    # 7. 근거 부족 시 할루시네이션 가드(LOW) 작동 테스트
    def test_evidence_matrix_low(self):
        tl = [{"message": "update", "diff_lines": [], "refs": [], "ref_details": [], "is_revert": False}]
        stats = calculate_evidence_strength(tl)
        self.assertEqual(stats["grade"], "LOW (근거 불충분)")
        self.assertLessEqual(stats["score"], 2)

if __name__ == "__main__":
    unittest.main()