import unittest

from claim_evidence import (
    BEHAVIOR,
    CONFLICTING,
    REVERT_CAUSE,
    SUPPORTED,
    UNVERIFIED,
    make_claim,
)
from claim_policy import (
    CONSERVATIVE,
    DIRECT,
    HIDDEN,
    collect_visible_claims,
    get_claim_visibility,
)


class TestClaimPolicy(unittest.TestCase):

    def make_supported_behavior(self):
        claim = make_claim(
            "o is encoded as UTF-8.",
            BEHAVIOR,
            [],
        )
        claim["status"] = SUPPORTED

        return claim

    def test_high_confidence_supported_claim_is_direct(self):
        claim = self.make_supported_behavior()

        stats = {
            "confidence": "VERY HIGH",
            "consistency": "HIGH",
            "is_blocked": False,
        }

        result = get_claim_visibility(
            claim,
            stats,
        )

        self.assertEqual(
            result,
            DIRECT,
        )

    def test_medium_confidence_supported_claim_is_conservative(self):
        claim = self.make_supported_behavior()

        stats = {
            "confidence": "MEDIUM",
            "consistency": "HIGH",
            "is_blocked": False,
        }

        result = get_claim_visibility(
            claim,
            stats,
        )

        self.assertEqual(
            result,
            CONSERVATIVE,
        )

    def test_unverified_claim_is_hidden(self):
        claim = make_claim(
            "The change improves performance.",
            BEHAVIOR,
            [],
        )
        claim["status"] = UNVERIFIED

        stats = {
            "confidence": "VERY HIGH",
            "consistency": "HIGH",
            "is_blocked": False,
        }

        result = get_claim_visibility(
            claim,
            stats,
        )

        self.assertEqual(
            result,
            HIDDEN,
        )

    def test_conflicting_claim_is_hidden(self):
        claim = self.make_supported_behavior()
        claim["status"] = CONFLICTING

        stats = {
            "confidence": "VERY HIGH",
            "consistency": "HIGH",
            "is_blocked": False,
        }

        result = get_claim_visibility(
            claim,
            stats,
        )

        self.assertEqual(
            result,
            HIDDEN,
        )

    def test_blocked_pipeline_hides_supported_claim(self):
        claim = self.make_supported_behavior()

        stats = {
            "confidence": "HIGH",
            "consistency": "HIGH",
            "is_blocked": True,
        }

        result = get_claim_visibility(
            claim,
            stats,
        )

        self.assertEqual(
            result,
            HIDDEN,
        )

    def test_inconsistent_pipeline_hides_supported_claim(self):
        claim = self.make_supported_behavior()

        stats = {
            "confidence": "VERY HIGH",
            "consistency": "INCONSISTENT",
            "is_blocked": False,
        }

        result = get_claim_visibility(
            claim,
            stats,
        )

        self.assertEqual(
            result,
            HIDDEN,
        )

    def test_low_confidence_hides_supported_claim(self):
        claim = self.make_supported_behavior()

        stats = {
            "confidence": "LOW",
            "consistency": "HIGH",
            "is_blocked": False,
        }

        result = get_claim_visibility(
            claim,
            stats,
        )

        self.assertEqual(
            result,
            HIDDEN,
        )

    def test_revert_cause_is_not_direct_even_with_high_confidence(self):
        claim = make_claim(
            "The change was reverted because it introduced a bug.",
            REVERT_CAUSE,
            [],
        )
        claim["status"] = SUPPORTED

        stats = {
            "confidence": "VERY HIGH",
            "consistency": "HIGH",
            "is_blocked": False,
        }

        result = get_claim_visibility(
            claim,
            stats,
        )

        self.assertEqual(
            result,
            CONSERVATIVE,
        )

    def test_visible_claims_preserve_visibility(self):
        direct_claim = self.make_supported_behavior()

        hidden_claim = make_claim(
            "The change improves performance.",
            BEHAVIOR,
            [],
        )
        hidden_claim["status"] = UNVERIFIED

        stats = {
            "confidence": "HIGH",
            "consistency": "HIGH",
            "is_blocked": False,
        }

        result = collect_visible_claims(
            [
                direct_claim,
                hidden_claim,
            ],
            stats,
        )

        self.assertEqual(
            len(result),
            1,
        )

        self.assertEqual(
            result[0]["visibility"],
            DIRECT,
        )

    def test_missing_confidence_hides_claim(self):
        claim = self.make_supported_behavior()

        stats = {
            "consistency": "HIGH",
            "is_blocked": False,
        }

        result = get_claim_visibility(
            claim,
            stats,
        )

        self.assertEqual(
            result,
            HIDDEN,
        )


if __name__ == "__main__":
    unittest.main()