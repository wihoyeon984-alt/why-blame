import unittest
from narrative import synthesize_narrative


class TestNarrative(unittest.TestCase):
    def test_single_commit_origin_narrative(self):
        """한 번도 수정되지 않은 원형 코드에 대한 서사 생성 검증"""
        timeline = [{"date": "2026-09-01", "hash": "c1a2b3c", "message": "feat: initial service", "ref_items": []}]
        headline, body = synthesize_narrative(timeline, {})
        self.assertIn("원형", headline)
        self.assertIn("원형 그대로 유지", body)
        self.assertIn("c1a2b3c", body)

    def test_revert_recovery_narrative(self):
        """롤백(Revert) 이력이 포함된 복구 코드에 대한 서사 생성 검증"""
        timeline = [
            {"date": "2026-01-01", "hash": "a111", "message": "feat: init", "is_revert": False, "type": "📍 FIRST OBSERVED"},
            {"date": "2026-01-02", "hash": "a222", "message": "fix: buggy change", "is_revert": True, "type": "↩ REVERT"},
            {"date": "2026-01-03", "hash": "a333", "message": "fix: safe recovery", "is_revert": False, "type": "🐛 BUG FIX",
             "ref_items": [{"number": 105, "type": "PR", "title": "Safe null check"}]}
        ]
        headline, body = synthesize_narrative(timeline, {})
        self.assertIn("롤백", headline)
        self.assertIn("롤백(a222)된 이력", body)
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
        self.assertIn("총 2단계", body)
        self.assertIn("b222", body)


if __name__ == "__main__":
    unittest.main()