import unittest
from timeline import classify_commit, calculate_evidence_strength, build_timeline

class TestTimeline(unittest.TestCase):
    
    # 1. 커밋 메시지 분류기 테스트
    def test_classify_commit(self):
        self.assertEqual(classify_commit("revert: cancel update", True), "↩ REVERT")
        self.assertEqual(classify_commit("fix: resolve null pointer exception", False), "🐛 BUG FIX")
        self.assertEqual(classify_commit("feat: add kakao login", False), "✨ FEATURE")
        self.assertEqual(classify_commit("refactor: cleanup user service", False), "🧹 REFACTOR")
        self.assertEqual(classify_commit("sec: update auth token policy", False), "🔒 SECURITY")
        self.assertEqual(classify_commit("random unhelpful message", False), "🔧 UPDATE")

    # 2. 증거 강도(Evidence Strength) 계산 테스트
    def test_evidence_strength(self):
        # 증거가 없는 단일 커밋 -> LOW
        weak_timeline = [{"is_revert": False, "diff_lines": [], "refs": []}]
        self.assertIn("LOW", calculate_evidence_strength(weak_timeline)["strength"])
        
        # 롤백 + 이슈 + Diff가 모두 있는 강력한 이력 -> VERY HIGH
        strong_timeline = [
            {"is_revert": True, "diff_lines": ["+ code"], "refs": ["101"]},
            {"is_revert": False, "diff_lines": ["- code"], "refs": ["202"]},
            {"is_revert": False, "diff_lines": ["+ code"], "refs": []},
        ]
        self.assertIn("VERY HIGH", calculate_evidence_strength(strong_timeline)["strength"])

    # 3. 시간순 정렬 및 탄생(BIRTH) 태깅 테스트
    def test_build_timeline_order(self):
        mock_commits = [
            {"message": "latest fix", "is_revert": False, "refs": []},
            {"message": "initial birth", "is_revert": False, "refs": []}
        ]
        timeline, _ = build_timeline(mock_commits, None, lambda o, r, n: "")
        
        # 첫 번째 커밋이 반드시 🌱 BIRTH여야 함
        self.assertEqual(timeline[0]["type"], "🌱 BIRTH")
        self.assertEqual(timeline[0]["message"], "initial birth")

if __name__ == "__main__":
    unittest.main()