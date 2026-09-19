import unittest
from narrative import synthesize_narrative


class TestNarrative(unittest.TestCase):
    def test_single_commit_origin_narrative(self):
        """한 번도 수정되지 않은 원형 코드에 대한 서사 생성 검증"""
        timeline = [{"date": "2026-09-01", "hash": "c1a2b3c", "message": "feat: initial service", "ref_items": []}]
        headline, body = synthesize_narrative(timeline, {})
        self.assertIn("원형", headline)
        self.assertIn("처음 관찰되었으며", body)
        self.assertIn("추가적인 수정 이력은 확인되지 않았습니다", body)
        self.assertIn("c1a2b3c", body)

    def test_revert_recovery_narrative(self):
        """롤백(Revert) 이력이 포함된 복구 코드에 대한 서사 생성 검증"""
        timeline = [
            {"date": "2026-01-01", "hash": "a111", "message": "feat: init", "is_revert": False, "type": "📍 FIRST OBSERVED"},
            {"date": "2026-01-02", "hash": "a222", "message": "revert: rollback bad commit", "is_revert": True, "type": "↩ REVERT"},
            {"date": "2026-01-03", "hash": "a333", "message": "fix: safe recovery", "is_revert": False, "type": "🐛 BUG FIX",
             "ref_items": [{"number": 105, "type": "PR", "title": "Safe null check"}]}
        ]
        headline, body = synthesize_narrative(timeline, {})
        self.assertIn("롤백", headline)
        self.assertIn("롤백 1회(a222", body)
        self.assertIn("PR #105", body)
        self.assertIn("a333", body)

    def test_evolution_bug_fix_narrative(self):
        """버그 수정을 거친 점진적 개선 코드에 대한 서사 생성 검증"""
        timeline = [
            {"date": "2026-01-01", "hash": "b111", "message": "feat: init", "is_revert": False, "type": "📍 FIRST OBSERVED"},
            {"date": "2026-01-02", "hash": "b222", "message": "fix: prevent race", "is_revert": False, "type": "🐛 BUG FIX",
             "ref_items": [{"number": 200, "type": "ISSUE", "title": "Race condition"}]}
        ]
        headline, body = synthesize_narrative(timeline, {})
        self.assertIn("결함 수정", headline)
        self.assertIn("b222", body)
        self.assertIn("PR #200", body)

    def test_complex_multi_event_narrative(self):
        """중간 사건(BUG FIX 2회, 롤백, FEATURE 등)이 누락 없이 서사에 들어가는지 검증"""
        timeline_6 = [
            {"date": "2026-01-01", "hash": "7c4ff0", "type": "📍 FIRST OBSERVED", "message": "feat: initial payment"},
            {"date": "2026-01-02", "hash": "2c17f74", "type": "🐛 BUG FIX", "message": "fix: check null"},
            {"date": "2026-01-03", "hash": "2f467c3", "type": "🐛 BUG FIX", "message": "fix: prevent race condition"},
            {"date": "2026-01-04", "hash": "8857c0c", "type": "↩ REVERT", "message": "revert: rollback temporary condition", "is_revert": True},
            {"date": "2026-01-05", "hash": "887d17e", "type": "✨ FEATURE", "message": "feat: add status check"},
            {"date": "2026-01-06", "hash": "f50e0a1", "type": "🔧 UPDATE", "message": "test: verify why-blame PR integration",
             "ref_items": [{"number": 1, "type": "PR", "title": "test: verify why-blame PR integration"}]}
        ]
        headline, body = synthesize_narrative(timeline_6, {})
        self.assertIn("결함 수정 2회", body)
        self.assertIn("2c17f74", body)
        self.assertIn("2f467c3", body)
        self.assertIn("롤백 1회", body)
        self.assertIn("8857c0c", body)
        self.assertIn("기능 추가 1회", body)
        self.assertIn("887d17e", body)
        self.assertIn("PR #1", body)
        self.assertNotIn("부작용 등으로", body)


if __name__ == "__main__":
    unittest.main()