"""Tests for Sprint 3 Autonomous Execution modules."""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from app.engineering.autonomous_executor import AutonomousExecutor, ExecutionMetrics
from app.engineering.qa_orchestrator import QAOrchestrator, QAReport, QACycleResult
from app.engineering.execution_monitor import ExecutionMonitor, ExecutionProgress, StageProgress
from app.engineering.workflow import EngineeringWorkflow, EngineeringWorkflowResult


class TestExecutionMetrics(unittest.TestCase):
    def test_metrics_initial_state(self):
        metrics = ExecutionMetrics()
        self.assertEqual(metrics.files_generated, 0)
        self.assertEqual(metrics.errors_fixed, 0)
        self.assertEqual(metrics.quality_score, 0.0)

    def test_metrics_to_dict(self):
        metrics = ExecutionMetrics(
            files_generated=10,
            tests_passed=5,
            tests_failed=1,
            errors_fixed=2,
            quality_score=85.0,
        )
        metrics.start_time = 1000.0
        metrics.end_time = 1010.0
        data = metrics.to_dict()
        self.assertEqual(data["files_generated"], 10)
        self.assertEqual(data["tests_passed"], 5)
        self.assertEqual(data["quality_score"], 85.0)
        self.assertEqual(data["duration_seconds"], 10.0)


class TestExecutionMonitor(unittest.TestCase):
    def test_start_and_complete(self):
        monitor = ExecutionMonitor()
        progress = monitor.start("exec-001", "Build Hospital")
        self.assertEqual(progress.execution_id, "exec-001")
        self.assertEqual(progress.overall_status, "running")

        monitor.stage_start("analysis")
        monitor.stage_complete("analysis", "Analysis done")
        monitor.complete(True, "Done")

        self.assertEqual(progress.overall_status, "completed")
        self.assertEqual(len(progress.stages), 1)
        self.assertEqual(progress.stages[0].status, "completed")

    def test_stage_failure(self):
        monitor = ExecutionMonitor()
        monitor.start("exec-002", "Build CRM")
        monitor.stage_start("generation")
        monitor.stage_fail("generation", "Disk full")
        monitor.complete(False, "Failed")

        self.assertEqual(monitor.get_progress().overall_status, "failed")
        self.assertEqual(monitor.get_progress().stages[0].status, "failed")

    def test_summary(self):
        monitor = ExecutionMonitor()
        monitor.start("exec-003", "Build Blog")
        monitor.stage_start("stage1")
        monitor.stage_complete("stage1")
        summary = monitor.get_summary()
        self.assertIn("exec-003", summary)
        self.assertIn("Build Blog", summary)


class TestQAOrchestrator(unittest.TestCase):
    def test_qa_orchestrator_initialization(self):
        qa = QAOrchestrator(quality_threshold=90.0, max_cycles=5)
        self.assertEqual(qa.quality_threshold, 90.0)
        self.assertEqual(qa.max_cycles, 5)

    def test_qa_report_structure(self):
        report = QAReport(project_path="/tmp/test", total_cycles=2, success=True)
        data = report.to_dict()
        self.assertEqual(data["project_path"], "/tmp/test")
        self.assertEqual(data["total_cycles"], 2)
        self.assertTrue(data["success"])

    def test_qa_cycle_result(self):
        cycle = QACycleResult(cycle=1, static_analysis_passed=True, tests_passed=True, quality_score=95.0)
        data = cycle.to_dict()
        self.assertTrue(data["static_analysis_passed"])
        self.assertTrue(data["tests_passed"])
        self.assertEqual(data["quality_score"], 95.0)

    @patch("app.engineering.qa_orchestrator.StaticAnalyzer")
    @patch("app.engineering.qa_orchestrator.TestEngine")
    def test_run_qa_loop(self, mock_test, mock_static):
        mock_analyzer = MagicMock()
        mock_analyzer.scan_directory.return_value = MagicMock(issues=[])
        mock_static.return_value = mock_analyzer

        mock_test_engine = MagicMock()
        mock_test_engine.run.return_value = MagicMock(success=True)
        mock_test.return_value = mock_test_engine

        qa = QAOrchestrator(quality_threshold=80.0, max_cycles=3)
        with tempfile.TemporaryDirectory() as tmpdir:
            report = qa.run(tmpdir)
            self.assertIsInstance(report, QAReport)
            self.assertTrue(report.success or len(report.cycles) > 0)


    @patch("app.engineering.qa_orchestrator.StaticAnalyzer")
    @patch("app.engineering.qa_orchestrator.TestEngine")
    def test_failed_tests_must_not_report_success(self, mock_test, mock_static):
        analyzer = MagicMock()
        analyzer.scan_directory.return_value = MagicMock(issues=[])
        mock_static.return_value = analyzer

        test_engine = MagicMock()
        test_engine.run.return_value = MagicMock(success=False, passed=False)
        mock_test.return_value = test_engine

        qa = QAOrchestrator(quality_threshold=80.0, max_cycles=1)
        with tempfile.TemporaryDirectory() as tmpdir:
            report = qa.run(tmpdir)

        self.assertTrue(report.static_analysis_passed)
        self.assertFalse(report.tests_passed)
        self.assertFalse(report.success)

    @patch("app.engineering.qa_orchestrator.StaticAnalyzer")
    @patch("app.engineering.qa_orchestrator.TestEngine")
    def test_static_analysis_failure_must_not_report_success(
        self, mock_test, mock_static
    ):
        analyzer = MagicMock()
        analyzer.scan_directory.return_value = MagicMock(
            issues=[MagicMock(
                category="test",
                severity="high",
                message="intentional test issue",
                file_path="example.py",
                line_number=1,
            )]
        )
        mock_static.return_value = analyzer

        test_engine = MagicMock()
        test_engine.run.return_value = MagicMock(success=True, passed=True)
        mock_test.return_value = test_engine

        qa = QAOrchestrator(quality_threshold=80.0, max_cycles=1)
        with tempfile.TemporaryDirectory() as tmpdir:
            report = qa.run(tmpdir)

        self.assertFalse(report.static_analysis_passed)
        self.assertTrue(report.tests_passed)
        self.assertFalse(report.success)


class TestAutonomousExecutor(unittest.TestCase):
    def test_executor_initialization(self):
        executor = AutonomousExecutor()
        self.assertIsNotNone(executor.project_builder)
        self.assertEqual(executor.max_qa_cycles, 3)

    def test_executor_with_custom_components(self):
        mock_builder = MagicMock()
        mock_qa = MagicMock()
        mock_orchestrator = MagicMock()

        executor = AutonomousExecutor(
            project_builder=mock_builder,
            qa_orchestrator=mock_qa,
            agent_orchestrator=mock_orchestrator,
            max_qa_cycles=5,
        )
        self.assertEqual(executor.max_qa_cycles, 5)
        self.assertEqual(executor.qa_orchestrator, mock_qa)

    def test_count_files(self):
        executor = AutonomousExecutor()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some files
            for i in range(3):
                with open(os.path.join(tmpdir, f"file{i}.py"), "w") as f:
                    f.write("# test")
            count = executor._count_files(tmpdir)
            self.assertEqual(count, 3)

    def test_count_files_empty_dir(self):
        executor = AutonomousExecutor()
        with tempfile.TemporaryDirectory() as tmpdir:
            count = executor._count_files(tmpdir)
            self.assertEqual(count, 0)

    def test_count_files_nonexistent(self):
        executor = AutonomousExecutor()
        count = executor._count_files("/nonexistent/path/12345")
        self.assertEqual(count, 0)


class TestEngineeringWorkflowIntegration(unittest.TestCase):
    def test_full_workflow_produces_executable_plan(self):
        workflow = EngineeringWorkflow()
        result = workflow.run("Build Hospital Management System")
        self.assertTrue(result.success)
        self.assertIsNotNone(result.analysis)
        self.assertIsNotNone(result.architecture)
        self.assertIsNotNone(result.tech_stack)
        self.assertIsNotNone(result.patterns)
        self.assertIsNotNone(result.risks)
        self.assertIsNotNone(result.complexity)

    def test_workflow_result_to_dict(self):
        workflow = EngineeringWorkflow()
        result = workflow.run("Build E-Commerce Platform")
        data = result.to_dict()
        self.assertIn("workflow_id", data)
        self.assertIn("analysis", data)
        self.assertIn("tech_stack", data)
        self.assertIn("patterns", data)
        self.assertIn("risks", data)
        self.assertIn("complexity", data)


if __name__ == "__main__":
    unittest.main()
