import unittest

from timeline import (
    classify_commit,
    calculate_evidence_strength,
    build_timeline,
    calculate_availability,
    calculate_consistency,
    calculate_source_reliability,
    calculate_history_ambiguity,
    decide_overall_confidence,
)


class TestTimeline(unittest.TestCase):

    # =========================================================
    # Commit classification
    # =========================================================

    def test_classify_conventional_commits(self):
        self.assertEqual(
            classify_commit("feat: add payment"),
            "✨ FEATURE"
        )

        self.assertEqual(
            classify_commit("fix: prevent duplicate charge"),
            "🐛 BUG FIX"
        )

        self.assertEqual(
            classify_commit("refactor: simplify payment flow"),
            "♻️ REFACTOR"
        )

        self.assertEqual(
            classify_commit("test: add payment tests"),
            "🧪 TEST"
        )

        self.assertEqual(
            classify_commit("docs: update README"),
            "📝 DOCS"
        )

        self.assertEqual(
            classify_commit("perf: optimize query"),
            "⚡ PERF"
        )

        self.assertEqual(
            classify_commit("security: validate token"),
            "🔒 SECURITY"
        )

    def test_classify_revert(self):
        self.assertEqual(
            classify_commit(
                "revert: rollback condition",
                is_revert=True
            ),
            "🔄 REVERT"
        )

        self.assertEqual(
            classify_commit(
                "Revert payment change"
            ),
            "🔄 REVERT"
        )

    def test_classify_keyword_fallback(self):
        self.assertEqual(
            classify_commit("prevent duplicate payment"),
            "🐛 BUG FIX"
        )

        self.assertEqual(
            classify_commit("implement user validation"),
            "✨ FEATURE"
        )

        self.assertEqual(
            classify_commit("cleanup old code"),
            "♻️ REFACTOR"
        )

        self.assertEqual(
            classify_commit("update configuration"),
            "📦 UPDATE"
        )

    # =========================================================
    # Evidence score
    # =========================================================

    def test_evidence_strength_low(self):
        timeline = [
            {
                "message": "x",
                "diff_lines": [],
                "ref_items": [],
                "is_revert": False
            }
        ]

        result = calculate_evidence_strength(timeline)

        self.assertEqual(result["score"], 0)
        self.assertEqual(result["grade"], "LOW")

    def test_evidence_strength_weak(self):
        timeline = [
            {
                "message": "fix payment",
                "diff_lines": ["+ charge()"],
                "ref_items": [],
                "is_revert": False
            }
        ]

        result = calculate_evidence_strength(timeline)

        self.assertEqual(result["score"], 4)
        self.assertEqual(result["grade"], "WEAK")

    def test_evidence_strength_moderate(self):
        timeline = [
            {
                "message": "fix payment race",
                "diff_lines": ["+ charge()"],
                "ref_items": [
                    {
                        "status": "SUCCESS",
                        "number": 101,
                        "type": "ISSUE",
                        "title": ""
                    }
                ],
                "is_revert": False
            }
        ]

        result = calculate_evidence_strength(timeline)

        self.assertEqual(result["score"], 7)
        self.assertEqual(result["grade"], "MODERATE")
        self.assertTrue(result["has_refs"])

    def test_evidence_strength_high(self):
        timeline = [
            {
                "message": "fix payment race",
                "diff_lines": ["+ charge()"],
                "ref_items": [
                    {
                        "status": "SUCCESS",
                        "number": 101,
                        "type": "ISSUE",
                        "title": "Payment Fix"
                    }
                ],
                "is_revert": False
            }
        ]

        result = calculate_evidence_strength(timeline)

        self.assertEqual(result["score"], 9)
        self.assertEqual(result["grade"], "HIGH")
        self.assertTrue(result["has_refs"])

    def test_evidence_strength_high_with_revert(self):
        timeline = [
            {
                "message": "fix payment race",
                "diff_lines": ["+ charge()"],
                "ref_items": [
                    {
                        "status": "SUCCESS",
                        "number": 101,
                        "type": "ISSUE",
                        "title": "Payment Fix"
                    }
                ],
                "is_revert": True
            }
        ]

        result = calculate_evidence_strength(timeline)

        self.assertEqual(result["score"], 9)
        self.assertEqual(result["grade"], "HIGH")

    def test_not_found_reference_is_not_evidence(self):
        timeline = [
            {
                "message": "fix payment",
                "diff_lines": ["+ charge()"],
                "ref_items": [
                    {
                        "status": "NOT_FOUND",
                        "number": 1347,
                        "type": "UNKNOWN",
                        "title": ""
                    }
                ],
                "is_revert": False
            }
        ]

        result = calculate_evidence_strength(timeline)

        self.assertEqual(result["score"], 4)
        self.assertFalse(result["has_refs"])

    def test_not_found_reference_does_not_count_as_fetched(self):
        timeline = [
            {
                "message": "fix payment",
                "diff_lines": ["+ charge()"],
                "ref_items": [
                    {
                        "status": "NOT_FOUND",
                        "number": 1347,
                        "type": "UNKNOWN",
                        "title": ""
                    }
                ],
                "is_revert": False
            }
        ]

        result = calculate_evidence_strength(timeline)

        self.assertFalse(result["has_refs"])
        self.assertEqual(result["score"], 4)

    def test_success_reference_is_evidence(self):
        timeline = [
            {
                "message": "fix payment",
                "diff_lines": ["+ charge()"],
                "ref_items": [
                    {
                        "status": "SUCCESS",
                        "number": 101,
                        "type": "ISSUE",
                        "title": ""
                    }
                ],
                "is_revert": False
            }
        ]

        result = calculate_evidence_strength(timeline)

        self.assertEqual(result["score"], 7)
        self.assertTrue(result["has_refs"])

    # =========================================================
    # Timeline
    # =========================================================

    def test_build_timeline_first_commit_observed(self):
        commits = [
            {
                "hash": "aaa111122223333",
                "message": "feat: initial payment",
                "diff_lines": ["+ charge()"],
                "refs": [],
                "is_revert": False
            },
            {
                "hash": "bbb111122223333",
                "message": "fix: payment bug",
                "diff_lines": [
                    "- charge()",
                    "+ safe_charge()"
                ],
                "refs": [],
                "is_revert": False
            }
        ]

        def fake_fetch_ref(owner, repo, number):
            return {
                "status": "NOT_FOUND",
                "number": number,
                "type": "UNKNOWN",
                "title": ""
            }

        timeline, stats = build_timeline(
            commits,
            ("wihoyeon984-alt", "why-blame"),
            fake_fetch_ref,
            lambda owner, repo, sha: []
        )

        self.assertEqual(
            timeline[0]["type"],
            "🌱 FIRST OBSERVED"
        )

        self.assertEqual(
            timeline[1]["type"],
            "✨ FEATURE"
        )

    def test_sha_lookup_finds_pr(self):
        commits = [
            {
                "hash": "abcdef1234567890",
                "message": "fix: payment",
                "diff_lines": ["+ charge()"],
                "refs": [],
                "is_revert": False
            }
        ]

        def fake_fetch_ref(owner, repo, number):
            raise AssertionError(
                "SHA 기반 PR 조회가 성공하면 "
                "#번호 fallback을 실행하면 안 됩니다."
            )

        def fake_fetch_commit_prs(owner, repo, sha):
            self.assertEqual(
                sha,
                "abcdef1234567890"
            )

            return [
                {
                    "status": "SUCCESS",
                    "number": 55,
                    "type": "PR",
                    "title": "Fix payment",
                    "body_summary": "",
                    "labels": [],
                    "state": "merged",
                    "url": "https://github.com/example"
                }
            ]

        timeline, stats = build_timeline(
            commits,
            ("wihoyeon984-alt", "why-blame"),
            fake_fetch_ref,
            fake_fetch_commit_prs
        )

        self.assertEqual(
            timeline[0]["ref_details"],
            ["PR #55 ('Fix payment')"]
        )

        self.assertEqual(
            timeline[0]["ref_items"][0]["status"],
            "SUCCESS"
        )

    def test_sha_lookup_without_issue_number(self):
        commits = [
            {
                "hash": "abcdef1234567890",
                "message": "fix: payment logic",
                "diff_lines": ["+ safe_charge()"],
                "refs": [],
                "is_revert": False
            }
        ]

        def fake_fetch_ref(owner, repo, number):
            raise AssertionError(
                "Issue 번호가 없으므로 "
                "#번호 fallback을 실행하면 안 됩니다."
            )

        def fake_fetch_commit_prs(owner, repo, sha):
            return [
                {
                    "status": "SUCCESS",
                    "number": 77,
                    "type": "PR",
                    "title": "Improve payment validation"
                }
            ]

        timeline, stats = build_timeline(
            commits,
            ("wihoyeon984-alt", "why-blame"),
            fake_fetch_ref,
            fake_fetch_commit_prs
        )

        self.assertEqual(
            timeline[0]["ref_details"],
            ["PR #77 ('Improve payment validation')"]
        )

    def test_sha_lookup_falls_back_to_commit_reference(self):
        commits = [
            {
                "hash": "abcdef1234567890",
                "message": "fix payment (#101)",
                "diff_lines": ["+ charge()"],
                "refs": [101],
                "is_revert": False
            }
        ]

        def fake_fetch_commit_prs(owner, repo, sha):
            return []

        def fake_fetch_ref(owner, repo, number):
            self.assertEqual(number, 101)

            return {
                "status": "SUCCESS",
                "number": 101,
                "type": "ISSUE",
                "title": "Payment Fix"
            }

        timeline, stats = build_timeline(
            commits,
            ("wihoyeon984-alt", "why-blame"),
            fake_fetch_ref,
            fake_fetch_commit_prs
        )

        self.assertEqual(
            timeline[0]["ref_details"],
            ["ISSUE #101 ('Payment Fix')"]
        )

        self.assertTrue(
            timeline[0]["ref_items"]
        )

    def test_not_found_reference_is_displayed_separately(self):
        commits = [
            {
                "hash": "abc123456789",
                "message": "fix payment (#1347)",
                "diff_lines": ["+ charge()"],
                "refs": [1347],
                "is_revert": False
            }
        ]

        def fake_fetch_ref(owner, repo, number):
            return {
                "status": "NOT_FOUND",
                "number": number,
                "type": "UNKNOWN",
                "title": "",
                "body_summary": "",
                "labels": [],
                "state": None,
                "url": None
            }

        timeline, stats = build_timeline(
            commits,
            ("wihoyeon984-alt", "why-blame"),
            fake_fetch_ref,
            lambda owner, repo, sha: []
        )

        self.assertEqual(
            timeline[0]["ref_details"],
            ["REF #1347 [NOT FOUND]"]
        )

        self.assertEqual(
            stats["score"],
            4
        )

    def test_revert_is_preserved(self):
        commits = [
            {
                "hash": "abc123456789",
                "message": "revert: rollback condition",
                "diff_lines": ["- old_condition"],
                "refs": [],
                "is_revert": True
            }
        ]

        def fake_fetch_ref(owner, repo, number):
            return {}

        timeline, stats = build_timeline(
            commits,
            ("wihoyeon984-alt", "why-blame"),
            fake_fetch_ref,
            lambda owner, repo, sha: []
        )

        self.assertEqual(
            timeline[0]["type"],
            "🌱 FIRST OBSERVED"
        )

        self.assertTrue(
            timeline[0]["is_revert"]
        )

    # =========================================================
    # Confidence Model v2
    # =========================================================

    def test_v2_availability_levels(self):
        self.assertEqual(
            calculate_availability(True, True, True, True),
            "HIGH"
        )
        self.assertEqual(
            calculate_availability(True, True, False, False),
            "MODERATE"
        )
        self.assertEqual(
            calculate_availability(False, False, False, False),
            "LOW"
        )

    def test_v2_unlinked_yields_weak_confidence(self):
        overall, blocked, limitations = decide_overall_confidence(
            "HIGH",
            "UNLINKED",
            "LOW",
            "LOW"
        )

        self.assertEqual(overall, "WEAK")
        self.assertFalse(blocked)

    def test_v2_inconsistent_blocks_why_and_yields_low(self):
        overall, blocked, limitations = decide_overall_confidence(
            "HIGH",
            "INCONSISTENT",
            "HIGH",
            "LOW"
        )

        self.assertTrue(overall.startswith("LOW"))
        self.assertTrue(blocked)
        self.assertTrue(len(limitations) > 0)

    def test_v2_high_consistency_with_low_availability_yields_moderate(self):
        overall, blocked, limitations = decide_overall_confidence(
            "LOW",
            "HIGH",
            "HIGH",
            "LOW"
        )

        self.assertEqual(overall, "MODERATE")
        self.assertFalse(blocked)

    def test_v2_revert_detected_caps_confidence_to_medium(self):
        overall, blocked, limitations = decide_overall_confidence(
            "HIGH",
            "HIGH",
            "HIGH",
            "HIGH"
        )

        self.assertEqual(overall, "MEDIUM")
        self.assertFalse(blocked)

        self.assertTrue(
            any(
                "Rollback" in item
                for item in limitations
            )
        )

    def test_v2_multiple_reverts_tracked_in_limitations(self):
        timeline = [
            {
                "message": "revert payment fix",
                "is_revert": True,
                "diff_lines": [],
                "ref_items": []
            },
            {
                "message": "revert previous change",
                "is_revert": True,
                "diff_lines": [],
                "ref_items": []
            }
        ]

        result = calculate_evidence_strength(timeline)

        self.assertTrue(
            result["has_rollback"]
        )

        self.assertEqual(
            result["history_ambiguity"],
            "HIGH"
        )

        self.assertEqual(
            len(result["report"].rollback_commits),
            2
        )

        self.assertTrue(
            any(
                "Rollback" in item
                for item in result["limitations"]
            )
        )


if __name__ == "__main__":
    unittest.main()