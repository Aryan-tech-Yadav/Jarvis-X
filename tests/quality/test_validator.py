"""Unit tests for Benchmark Validator, Quality Score Engine, and Quality Report."""

import tempfile
import unittest
from pathlib import Path

from app.quality.benchmark_validator import BenchmarkValidator
from app.quality.models import (
    CoverageResult,
    PerformanceResult,
    QualityCategory,
    SecurityResult,
    TestSuiteResult,
)
from app.quality.quality_report import QualityReport
from app.quality.quality_score import QualityScoreEngine


class TestValidatorAndScoring(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_benchmark_validator_records_and_trends(self):
        validator = BenchmarkValidator(str(self.root / "knowledge"))
        run1 = validator.record_run("v0.8", 90.0, 91.0, 92.0, 90.0, 95.0, 90.0, "A")
        run2 = validator.record_run("v0.9", 94.0, 95.0, 96.0, 94.0, 98.0, 95.0, "A+")

        self.assertEqual(len(validator.get_history()), 2)
        passed, regressions = validator.compare_with_baseline(run2)
        self.assertTrue(passed)

        trend_text = validator.generate_trend_graph()
        self.assertIn("v0.8", trend_text)
        self.assertIn("v0.9", trend_text)

    def test_quality_score_engine_calculation_and_gate_pass(self):
        scorer = QualityScoreEngine()
        ts = TestSuiteResult(
            total_tests=10,
            passed=10,
            failed=0,
            coverage=CoverageResult(100, 95, 95.0),
            success=True,
        )
        sec = SecurityResult(passed=True, security_score=100.0)
        perf = PerformanceResult(performance_score=95.0)

        score = scorer.compute_overall_score(
            architecture_score=95.0,
            code_quality_score=95.0,
            test_suite_result=ts,
            security_result=sec,
            performance_result=perf,
            documentation_score=95.0,
        )

        self.assertGreaterEqual(score.overall_score, 90.0)
        self.assertTrue(score.passed_gate)
        self.assertIn(score.grade, ["A", "A+"])

    def test_quality_score_engine_rejection_on_vulnerability(self):
        scorer = QualityScoreEngine()
        sec = SecurityResult(passed=False, security_score=50.0)

        score = scorer.compute_overall_score(
            architecture_score=95.0,
            code_quality_score=95.0,
            security_result=sec,
        )

        self.assertFalse(score.passed_gate)
        self.assertTrue(any("security" in r.lower() for r in score.gate_reasons))

    def test_quality_report_export_formats(self):
        scorer = QualityScoreEngine()
        score = scorer.compute_overall_score(92.0, 94.0)
        report = QualityReport(project_name="DemoApp", quality_score=score)

        md = report.to_markdown()
        self.assertIn("Autonomous Quality & Self-Healing Report", md)
        self.assertIn("Category Scoreboard", md)

        yaml_str = report.to_yaml()
        self.assertIn("quality_score:", yaml_str)

        json_str = report.to_json()
        self.assertIn('"project_name": "DemoApp"', json_str)
