import unittest
from timeline import classify_commit, calculate_evidence_strength, build_timeline


class TestTimeline(unittest.TestCase):
    def test_classify_conventional_commits(self):
        """feat, fix, revert 등 커밋 메시지 프리픽스 자동 분류 검증"""
        self.assertEqual(classify_commit("feat: add login feature"), "✨ FEATURE")
        self.assertEqual(classify_commit("fix: resolve payment issue"), "🐛 BUG FIX")
        self.assertEqual(classify_commit("revert: rollback bad commit"), "↩ REVERT")
        self.assertEqual(classify_commit("refactor: clean up db layer"), "🧹 REFACTOR")
        self.assertEqual(classify_commit("docs: update README"), "📝 DOCS")
        self.assertEqual(classify_commit("is_revert flag true", is_revert=True), "↩ REVERT")

    def test_classify_keyword_fallback(self):
        """접두어가 없는 일반 커밋 메시지의 키워드 기반 분류 검증"""
        self.assertEqual(classify_commit("prevent race condition in billing"), "🐛 BUG FIX")
        self.assertEqual(classify_commit("add support for oauth2"), "✨ FEATURE")
        self.assertEqual(classify_commit("cleanup unused imports"), "🧹 REFACTOR")
        self.assertEqual(classify_commit("bump version number"), "🔧 UPDATE")

    def test_evidence_strength_grades(self):
        """README 명세에 정의된 5단계 증거 점수 구간 검증"""
        # 점수 0점 -> LOW
        self.assertEqual(calculate_evidence_strength([])["grade"], "LOW")

        # 점수 3점 (message>5 [+1] + diff_lines [+2]) -> WEAK
        timeline_weak = [{"message": "fix payment race", "diff_lines": ["+ charge()"]}]
        self.assertEqual(calculate_evidence_strength(timeline_weak)["grade"], "WEAK")

        # 점수 6점 (message [+1] + diff [+2] + refs [+3]) -> MODERATE
        timeline_mod = [{"message": "fix payment race", "diff_lines": ["+ charge()"], "refs": [101]}]
        self.assertEqual(calculate_evidence_strength(timeline_mod)["grade"], "MODERATE")

        # 점수 9점 (message [+1] + diff [+2] + refs [+3] + revert [+3]) -> HIGH
        timeline_high = [{"message": "fix payment race", "diff_lines": ["+ charge()"], "refs": [101], "is_revert": True}]
        self.assertEqual(calculate_evidence_strength(timeline_high)["grade"], "HIGH")

        # 점수 11점 (message [+1] + diff [+2] + refs [+3] + fetched [+2] + revert [+3]) -> VERY HIGH
        timeline_vhigh = [{
            "message": "fix payment race",
            "diff_lines": ["+ charge()"],
            "refs": [101],
            "ref_details": ["#101 ('Payment Fix')"],
            "is_revert": True
        }]
        self.assertEqual(calculate_evidence_strength(timeline_vhigh)["grade"], "VERY HIGH")

    def test_build_timeline_first_commit_birth(self):
        """첫 번째 커밋에 🌱 BIRTH 타입이 부여되는지 검증"""
        sample_commits = [
            {"hash": "aaa", "date": "2026-09-01", "message": "second", "is_revert": False, "refs": [], "diff_lines": []},
            {"hash": "bbb", "date": "2026-08-01", "message": "first", "is_revert": False, "refs": [], "diff_lines": []},
        ]
        timeline, stats = build_timeline(sample_commits, None, lambda o, r, n: "")
        self.assertEqual(timeline[0]["type"], "🌱 BIRTH")
        self.assertEqual(timeline["type"], "🔧 UPDATE")


if __name__ == "__main__":
    unittest.main()