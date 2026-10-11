import json
import tempfile
import unittest
from pathlib import Path

from benchmark.holdout.score_holdout import (
    CaseAnnotation,
    ClaimAnnotation,
    GroundTruthClaim,
    HoldoutCase,
    ScoringError,
    compute_metrics,
    discover_cases,
    load_annotation,
    safe_divide,
    summarize_ground_truth,
)


class TestHoldoutScoring(unittest.TestCase):

    def make_case(
        self,
        case_id="case_001",
        claims=None,
        required_abstentions=0,
    ):
        if claims is None:
            claims = (
                GroundTruthClaim(
                    "claim_001",
                    "SUPPORTED",
                ),
            )

        return HoldoutCase(
            case_id=case_id,
            path=Path(f"{case_id}.yaml"),
            frozen=True,
            frozen_before_system_run=True,
            implementation_commit="2c4bf34",
            claims=tuple(claims),
            required_abstentions=required_abstentions,
        )

    def test_safe_divide_zero_denominator_returns_none(self):
        self.assertIsNone(
            safe_divide(1, 0)
        )

    def test_ground_truth_summary_counts_labels(self):
        case = self.make_case(
            claims=(
                GroundTruthClaim(
                    "claim_001",
                    "SUPPORTED",
                ),
                GroundTruthClaim(
                    "claim_002",
                    "UNSUPPORTED",
                ),
                GroundTruthClaim(
                    "claim_003",
                    "AMBIGUOUS",
                ),
                GroundTruthClaim(
                    "claim_004",
                    "CONFLICTING",
                ),
            ),
            required_abstentions=3,
        )

        result = summarize_ground_truth([case])

        self.assertEqual(result["cases"], 1)
        self.assertEqual(
            result["total_claims"],
            4,
        )
        self.assertEqual(
            result["supported"],
            1,
        )
        self.assertEqual(
            result["unsupported"],
            1,
        )
        self.assertEqual(
            result["ambiguous"],
            1,
        )
        self.assertEqual(
            result["conflicting"],
            1,
        )
        self.assertEqual(
            result["required_abstentions"],
            3,
        )

    def test_not_reached_is_not_observable_supported(self):
        case = self.make_case()

        annotation = CaseAnnotation(
            case_id="case_001",
            completed=False,
            failure_stage="HISTORY_RENDERING",
            failure_type="UnicodeEncodeError",
            claims={
                "claim_001": ClaimAnnotation(
                    status="NOT_REACHED",
                    raw_evidence="",
                )
            },
        )

        result = compute_metrics(
            [case],
            {"case_001": annotation},
        )

        self.assertEqual(
            result["supported_total"],
            1,
        )
        self.assertEqual(
            result["supported_presented"],
            0,
        )
        self.assertEqual(
            result["observable_supported"],
            0,
        )
        self.assertIsNone(
            result["observed_supported_recall"]
        )
        self.assertEqual(
            result["strict_supported_recall"],
            0.0,
        )
        self.assertEqual(
            result["unobservable_claim_rate"],
            1.0,
        )

    def test_supported_presented_counts_in_both_recall_metrics(self):
        case = self.make_case()

        annotation = CaseAnnotation(
            case_id="case_001",
            completed=False,
            failure_stage="HISTORY_RENDERING",
            failure_type="UnicodeEncodeError",
            claims={
                "claim_001": ClaimAnnotation(
                    status="PRESENTED",
                    raw_evidence="visible behavior",
                )
            },
        )

        result = compute_metrics(
            [case],
            {"case_001": annotation},
        )

        self.assertEqual(
            result["strict_supported_recall"],
            1.0,
        )
        self.assertEqual(
            result["observed_supported_recall"],
            1.0,
        )
        self.assertEqual(
            result["safe_claim_coverage"],
            1.0,
        )

    def test_correct_abstention_counts_for_unsupported_claim(self):
        case = self.make_case(
            claims=(
                GroundTruthClaim(
                    "claim_001",
                    "UNSUPPORTED",
                ),
            ),
            required_abstentions=1,
        )

        annotation = CaseAnnotation(
            case_id="case_001",
            completed=False,
            failure_stage="HISTORY_RENDERING",
            failure_type="UnicodeEncodeError",
            claims={
                "claim_001": ClaimAnnotation(
                    status="ABSTAINED",
                    raw_evidence="WHY not generated",
                )
            },
        )

        result = compute_metrics(
            [case],
            {"case_001": annotation},
        )

        self.assertEqual(
            result["correct_abstentions"],
            1,
        )
        self.assertEqual(
            result["system_abstentions"],
            1,
        )
        self.assertEqual(
            result["required_abstentions"],
            1,
        )
        self.assertEqual(
            result["abstention_precision"],
            1.0,
        )
        self.assertEqual(
            result["abstention_recall"],
            1.0,
        )

    def test_abstaining_from_supported_claim_is_not_correct(self):
        case = self.make_case()

        annotation = CaseAnnotation(
            case_id="case_001",
            completed=False,
            failure_stage="HISTORY_RENDERING",
            failure_type="UnicodeEncodeError",
            claims={
                "claim_001": ClaimAnnotation(
                    status="ABSTAINED",
                    raw_evidence="",
                )
            },
        )

        result = compute_metrics(
            [case],
            {"case_001": annotation},
        )

        self.assertEqual(
            result["correct_abstentions"],
            0,
        )
        self.assertEqual(
            result["system_abstentions"],
            1,
        )
        self.assertEqual(
            result["abstention_precision"],
            0.0,
        )

    def test_invalid_annotation_status_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "annotation.json"

            path.write_text(
                json.dumps(
                    {
                        "case_id": "case_001",
                        "execution": {
                            "completed": False,
                        },
                        "claims": {
                            "claim_001": {
                                "status": "MAYBE",
                                "raw_evidence": "",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ScoringError):
                load_annotation(path)

    def test_real_holdout_ground_truth_totals(self):
        cases_dir = (
            Path(__file__).resolve().parent
            / "benchmark"
            / "holdout"
            / "cases"
        )

        cases = discover_cases(cases_dir)
        result = summarize_ground_truth(cases)

        self.assertEqual(result["cases"], 10)
        self.assertEqual(
            result["total_claims"],
            55,
        )
        self.assertEqual(
            result["supported"],
            32,
        )
        self.assertEqual(
            result["unsupported"],
            19,
        )
        self.assertEqual(
            result["ambiguous"],
            4,
        )
        self.assertEqual(
            result["conflicting"],
            0,
        )
        self.assertEqual(
            result["required_abstentions"],
            23,
        )


if __name__ == "__main__":
    unittest.main()