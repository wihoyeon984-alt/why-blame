import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout


ROOT = Path(__file__).resolve().parent

SCORER_PATH = (
    ROOT
    / "benchmark"
    / "holdout"
    / "score_holdout.py"
)

SPEC = importlib.util.spec_from_file_location(
    "score_holdout",
    SCORER_PATH,
)

score_holdout = importlib.util.module_from_spec(SPEC)

assert SPEC.loader is not None

sys.modules[SPEC.name] = score_holdout

SPEC.loader.exec_module(score_holdout)


class TestHoldoutScoring(unittest.TestCase):

    def test_real_holdout_ground_truth_totals(self):
        holdout_dir = (
            ROOT
            / "benchmark"
            / "holdout"
        )

        cases = score_holdout.discover_cases(
            holdout_dir / "cases"
        )

        summary = (
            score_holdout.summarize_ground_truth(
                cases
            )
        )

        self.assertEqual(
            summary["cases"],
            10,
        )
        self.assertEqual(
            summary["total_claims"],
            55,
        )
        self.assertEqual(
            summary["supported"],
            32,
        )
        self.assertEqual(
            summary["unsupported"],
            19,
        )
        self.assertEqual(
            summary["ambiguous"],
            4,
        )
        self.assertEqual(
            summary["conflicting"],
            0,
        )
        self.assertEqual(
            summary["required_abstentions"],
            23,
        )

    def test_real_holdout_has_ten_first_run_outputs(self):
        holdout_dir = (
            ROOT
            / "benchmark"
            / "holdout"
        )

        results = score_holdout.discover_results(
            holdout_dir / "results"
        )

        self.assertEqual(
            len(results),
            10,
        )

    def test_missing_annotations_are_incomplete(self):
        case = score_holdout.HoldoutCase(
            case_id="case_001",
            path=Path("case_001.yaml"),
            frozen=True,
            frozen_before_system_run=True,
            implementation_commit="2c4bf34",
            claims=(
                score_holdout.GroundTruthClaim(
                    claim_id="claim_001",
                    label="SUPPORTED",
                ),
            ),
            required_abstentions=0,
        )

        metrics = score_holdout.compute_metrics(
            [case],
            {},
        )

        self.assertEqual(
            metrics["annotated_cases"],
            0,
        )
        self.assertEqual(
            metrics["annotated_claims"],
            0,
        )
        self.assertFalse(
            metrics["annotation_complete"]
        )

    def test_not_reached_is_not_observable_supported(self):
        case = score_holdout.HoldoutCase(
            case_id="case_001",
            path=Path("case_001.yaml"),
            frozen=True,
            frozen_before_system_run=True,
            implementation_commit="2c4bf34",
            claims=(
                score_holdout.GroundTruthClaim(
                    claim_id="claim_001",
                    label="SUPPORTED",
                ),
            ),
            required_abstentions=0,
        )

        annotation = score_holdout.CaseAnnotation(
            case_id="case_001",
            completed=False,
            failure_stage="HISTORY_RENDERING",
            failure_type="UnicodeEncodeError",
            claims={
                "claim_001": (
                    score_holdout.ClaimAnnotation(
                        status="NOT_REACHED",
                        raw_evidence="",
                    )
                ),
            },
        )

        metrics = score_holdout.compute_metrics(
            [case],
            {
                "case_001": annotation,
            },
        )

        self.assertEqual(
            metrics["not_reached"],
            1,
        )
        self.assertEqual(
            metrics["observable_supported"],
            0,
        )
        self.assertIsNone(
            metrics["observed_supported_recall"]
        )

    def test_presented_supported_claim_is_recovered(self):
        case = score_holdout.HoldoutCase(
            case_id="case_001",
            path=Path("case_001.yaml"),
            frozen=True,
            frozen_before_system_run=True,
            implementation_commit="2c4bf34",
            claims=(
                score_holdout.GroundTruthClaim(
                    claim_id="claim_001",
                    label="SUPPORTED",
                ),
            ),
            required_abstentions=0,
        )

        annotation = score_holdout.CaseAnnotation(
            case_id="case_001",
            completed=False,
            failure_stage="HISTORY_RENDERING",
            failure_type="UnicodeEncodeError",
            claims={
                "claim_001": (
                    score_holdout.ClaimAnnotation(
                        status="PRESENTED",
                        raw_evidence=(
                            "visible before crash"
                        ),
                    )
                ),
            },
        )

        metrics = score_holdout.compute_metrics(
            [case],
            {
                "case_001": annotation,
            },
        )

        self.assertEqual(
            metrics["strict_supported_recall"],
            1.0,
        )
        self.assertEqual(
            metrics["observed_supported_recall"],
            1.0,
        )
        self.assertEqual(
            metrics["safe_claim_coverage"],
            1.0,
        )
        self.assertTrue(
            metrics["annotation_complete"]
        )

    def test_correct_abstention_is_counted(self):
        case = score_holdout.HoldoutCase(
            case_id="case_001",
            path=Path("case_001.yaml"),
            frozen=True,
            frozen_before_system_run=True,
            implementation_commit="2c4bf34",
            claims=(
                score_holdout.GroundTruthClaim(
                    claim_id="claim_001",
                    label="UNSUPPORTED",
                ),
            ),
            required_abstentions=1,
        )

        annotation = score_holdout.CaseAnnotation(
            case_id="case_001",
            completed=False,
            failure_stage="HISTORY_RENDERING",
            failure_type="UnicodeEncodeError",
            claims={
                "claim_001": (
                    score_holdout.ClaimAnnotation(
                        status="ABSTAINED",
                        raw_evidence=(
                            "explicit abstention"
                        ),
                    )
                ),
            },
        )

        metrics = score_holdout.compute_metrics(
            [case],
            {
                "case_001": annotation,
            },
        )

        self.assertEqual(
            metrics["correct_abstentions"],
            1,
        )
        self.assertEqual(
            metrics["system_abstentions"],
            1,
        )
        self.assertEqual(
            metrics["abstention_precision"],
            1.0,
        )
        self.assertEqual(
            metrics["abstention_recall"],
            1.0,
        )

        self.assertEqual(
            metrics["false_why"],
            0,
        )

    def test_semantic_metrics_are_not_scoreable_when_annotation_incomplete(self):
        case = score_holdout.HoldoutCase(
            case_id="case_001",
            path=Path("case_001.yaml"),
            frozen=True,
            frozen_before_system_run=True,
            implementation_commit="2c4bf34",
            claims=(
                score_holdout.GroundTruthClaim(
                    claim_id="claim_001",
                    label="SUPPORTED",
                ),
                score_holdout.GroundTruthClaim(
                    claim_id="claim_002",
                    label="UNSUPPORTED",
                ),
            ),
            required_abstentions=1,
        )

        annotation = score_holdout.CaseAnnotation(
            case_id="case_001",
            completed=False,
            failure_stage="HISTORY_RENDERING",
            failure_type="UnicodeEncodeError",
            claims={
                "claim_001": score_holdout.ClaimAnnotation(
                    status="PRESENTED",
                    raw_evidence="visible before crash",
                ),
            },
        )

        metrics = score_holdout.compute_metrics(
            [case],
            {
                "case_001": annotation,
            },
        )

        self.assertFalse(
            metrics["annotation_complete"]
        )
        self.assertFalse(
            score_holdout.semantic_metrics_scoreable(
                metrics
            )
        )

    def test_semantic_metrics_are_scoreable_when_annotation_complete(self):
        case = score_holdout.HoldoutCase(
            case_id="case_001",
            path=Path("case_001.yaml"),
            frozen=True,
            frozen_before_system_run=True,
            implementation_commit="2c4bf34",
            claims=(
                score_holdout.GroundTruthClaim(
                    claim_id="claim_001",
                    label="SUPPORTED",
                ),
                score_holdout.GroundTruthClaim(
                    claim_id="claim_002",
                    label="UNSUPPORTED",
                ),
            ),
            required_abstentions=1,
        )

        annotation = score_holdout.CaseAnnotation(
            case_id="case_001",
            completed=False,
            failure_stage="HISTORY_RENDERING",
            failure_type="UnicodeEncodeError",
            claims={
                "claim_001": score_holdout.ClaimAnnotation(
                    status="PRESENTED",
                    raw_evidence="visible before crash",
                ),
                "claim_002": score_holdout.ClaimAnnotation(
                    status="ABSTAINED",
                    raw_evidence="explicit abstention",
                ),
            },
        )

        metrics = score_holdout.compute_metrics(
            [case],
            {
                "case_001": annotation,
            },
        )

        self.assertTrue(
            metrics["annotation_complete"]
        )
        self.assertTrue(
            score_holdout.semantic_metrics_scoreable(
                metrics
            )
        )


    def test_report_hides_semantic_metrics_when_annotation_incomplete(self):
        ground_truth = {
            "cases": 1,
            "total_claims": 2,
            "supported": 1,
            "unsupported": 1,
            "ambiguous": 0,
            "conflicting": 0,
            "required_abstentions": 1,
        }

        exposure = {
            "PRESENTED": 1,
            "UNANNOTATED": 1,
        }

        metrics = {
            "e2e_completion_rate": 0.0,
            "strict_supported_recall": 1.0,
            "observed_supported_recall": 1.0,
            "unobservable_claim_rate": 0.0,
            "safe_claim_coverage": 0.5,
            "abstention_precision": None,
            "abstention_recall": 0.0,
            "unsafe_presented": 0,
            "annotated_cases": 1,
            "total_cases": 1,
            "annotated_claims": 1,
            "total_claims": 2,
            "annotation_complete": False,
        }

        output = io.StringIO()

        with redirect_stdout(output):
            score_holdout.print_report(
                ground_truth,
                exposure,
                metrics,
            )

        rendered = output.getvalue()

        self.assertIn(
            "E2E completion:",
            rendered,
        )
        self.assertIn(
            "Semantic metrics:",
            rendered,
        )
        self.assertIn(
            "NOT SCORED",
            rendered,
        )
        self.assertIn(
            "annotations incomplete (1/2)",
            rendered,
        )
        self.assertNotIn(
            "Strict supported recall:",
            rendered,
        )
        self.assertNotIn(
            "Abstention recall:",
            rendered,
        )

    def test_report_shows_semantic_metrics_when_annotation_complete(self):
        ground_truth = {
            "cases": 1,
            "total_claims": 2,
            "supported": 1,
            "unsupported": 1,
            "ambiguous": 0,
            "conflicting": 0,
            "required_abstentions": 1,
        }

        exposure = {
            "PRESENTED": 1,
            "ABSTAINED": 1,
        }

        metrics = {
            "e2e_completion_rate": 0.0,
            "strict_supported_recall": 1.0,
            "observed_supported_recall": 1.0,
            "unobservable_claim_rate": 0.0,
            "safe_claim_coverage": 0.5,
            "abstention_precision": 1.0,
            "abstention_recall": 1.0,
            "unsafe_presented": 0,
            "false_why": 0,
            "annotated_cases": 1,
            "total_cases": 1,
            "annotated_claims": 2,
            "total_claims": 2,
            "annotation_complete": True,
        }

        output = io.StringIO()

        with redirect_stdout(output):
            score_holdout.print_report(
                ground_truth,
                exposure,
                metrics,
            )

        rendered = output.getvalue()

        self.assertNotIn(
            "NOT SCORED",
            rendered,
        )
        self.assertIn(
            "Strict supported recall:",
            rendered,
        )
        self.assertIn(
            "Observed supported recall:",
            rendered,
        )
        self.assertIn(
            "Abstention recall:",
            rendered,
        )


        self.assertIn(
            "False-WHY:              0",
            rendered,
        )

    def test_withheld_is_valid_exposure_status(self):
        self.assertIn(
            "WITHHELD",
            score_holdout.VALID_EXPOSURE_STATUSES,
        )

    def test_withheld_is_safe_suppression_but_not_abstention(self):
        case = score_holdout.HoldoutCase(
            case_id="case_001",
            path=Path("case_001.yaml"),
            frozen=True,
            frozen_before_system_run=True,
            implementation_commit="2c4bf34",
            claims=(
                score_holdout.GroundTruthClaim(
                    claim_id="claim_001",
                    label="UNSUPPORTED",
                ),
            ),
            required_abstentions=1,
        )

        annotation = score_holdout.CaseAnnotation(
            case_id="case_001",
            completed=False,
            failure_stage="HISTORY_RENDERING",
            failure_type="UnicodeEncodeError",
            claims={
                "claim_001": (
                    score_holdout.ClaimAnnotation(
                        status="WITHHELD",
                        raw_evidence=(
                            "Unsafe claim was not presented, "
                            "but no explicit abstention was emitted."
                        ),
                    )
                ),
            },
        )

        metrics = score_holdout.compute_metrics(
            [case],
            {
                "case_001": annotation,
            },
        )

        self.assertEqual(
            metrics["system_abstentions"],
            0,
        )
        self.assertEqual(
            metrics["correct_abstentions"],
            0,
        )
        self.assertEqual(
            metrics["withheld"],
            1,
        )
        self.assertEqual(
            metrics["safe_suppressions"],
            1,
        )
        self.assertEqual(
            metrics["required_abstentions"],
            1,
        )


    def test_missed_is_valid_exposure_status(self):
        self.assertIn(
            "MISSED",
            score_holdout.VALID_EXPOSURE_STATUSES,
        )


    def test_unsafe_presented_unsupported_claim_is_false_why(self):
        case = score_holdout.HoldoutCase(
            case_id="case_001",
            path=Path("case_001.yaml"),
            frozen=True,
            frozen_before_system_run=True,
            implementation_commit="2c4bf34",
            claims=(
                score_holdout.GroundTruthClaim(
                    claim_id="claim_001",
                    label="UNSUPPORTED",
                ),
            ),
            required_abstentions=1,
        )

        annotation = score_holdout.CaseAnnotation(
            case_id="case_001",
            completed=True,
            failure_stage="",
            failure_type="",
            claims={
                "claim_001": score_holdout.ClaimAnnotation(
                    status="UNSAFE_PRESENTED",
                    raw_evidence="unsupported WHY was presented",
                ),
            },
        )

        metrics = score_holdout.compute_metrics(
            [case],
            {"case_001": annotation},
        )

        self.assertEqual(
            metrics["unsafe_presented"],
            1,
        )
        self.assertEqual(
            metrics["false_why"],
            1,
        )
        self.assertEqual(
            metrics["correct_abstentions"],
            0,
        )

    def test_missed_supported_claim_is_observable_failure(self):
        case = score_holdout.HoldoutCase(
            case_id="case_001",
            path=Path("case_001.yaml"),
            frozen=True,
            frozen_before_system_run=True,
            implementation_commit="2c4bf34",
            claims=(
                score_holdout.GroundTruthClaim(
                    claim_id="claim_001",
                    label="SUPPORTED",
                ),
            ),
            required_abstentions=0,
        )

        annotation = score_holdout.CaseAnnotation(
            case_id="case_001",
            completed=False,
            failure_stage="HISTORY_RENDERING",
            failure_type="UnicodeEncodeError",
            claims={
                "claim_001": (
                    score_holdout.ClaimAnnotation(
                        status="MISSED",
                        raw_evidence=(
                            "The relevant WHY output was observable "
                            "before the crash, but the supported "
                            "claim was not recovered."
                        ),
                    )
                ),
            },
        )

        metrics = score_holdout.compute_metrics(
            [case],
            {
                "case_001": annotation,
            },
        )

        self.assertEqual(
            metrics["supported_presented"],
            0,
        )
        self.assertEqual(
            metrics["observable_supported"],
            1,
        )
        self.assertEqual(
            metrics["strict_supported_recall"],
            0.0,
        )
        self.assertEqual(
            metrics["observed_supported_recall"],
            0.0,
        )
        self.assertEqual(
            metrics["not_reached"],
            0,
        )

    def test_parser_defaults_to_first_run(self):
        args = score_holdout.build_parser().parse_args([])
        self.assertEqual(args.run, "first")

    def test_parser_accepts_current_run(self):
        args = score_holdout.build_parser().parse_args(
            ["--run", "current"]
        )
        self.assertEqual(args.run, "current")

    def test_resolve_run_dirs_selects_first_and_current(self):
        holdout_dir = Path("holdout")

        first_results, first_scoring = (
            score_holdout.resolve_run_dirs(
                holdout_dir,
                "first",
            )
        )
        current_results, current_scoring = (
            score_holdout.resolve_run_dirs(
                holdout_dir,
                "current",
            )
        )

        self.assertEqual(
            first_results,
            holdout_dir / "results",
        )
        self.assertEqual(
            first_scoring,
            holdout_dir / "scoring",
        )
        self.assertEqual(
            current_results,
            holdout_dir / "current_run",
        )
        self.assertEqual(
            current_scoring,
            holdout_dir / "current_scoring",
        )

    def test_run_commit_metadata_is_not_discovered_as_result(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            results_dir = Path(temp_dir)
            (results_dir / "case_001.txt").write_text(
                "case output",
                encoding="utf-8",
            )
            (results_dir / "RUN_COMMIT.txt").write_text(
                "abcdef1",
                encoding="utf-8",
            )

            results = score_holdout.discover_results(
                results_dir
            )

            self.assertEqual(
                set(results),
                {"case_001"},
            )

if __name__ == "__main__":
    unittest.main()
