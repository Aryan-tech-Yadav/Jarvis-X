"""Integration test for Sprint 9 - Autonomous Project Runtime.

Verifies the complete execution flow:
  1. Runtime Session creation
  2. Checkpoint creation and recovery
  3. Artifact management
  4. Progress tracking
  5. Retry management
  6. Runtime events
  7. Metrics collection (benchmark, code, performance, quality)
  8. Learning engine integration
  9. Improvement engine comparison
  10. Final report generation

Also tests crash recovery: if execution crashes at 70%,
the next run should resume from the last checkpoint.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from typing import Any, Dict

import pytest


@pytest.fixture
def temp_jarvis_dir():
    """Create a temporary directory for Jarvis data."""
    temp_dir = tempfile.mkdtemp(prefix="jarvis_test_")
    original_dir = os.getcwd()
    os.chdir(temp_dir)

    # Create required directories
    os.makedirs(".jarvis/sessions", exist_ok=True)
    os.makedirs(".jarvis/checkpoints", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("artifacts", exist_ok=True)
    os.makedirs(".jarvis/events", exist_ok=True)

    yield temp_dir

    os.chdir(original_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestRuntimeSession:
    """Test runtime session management."""

    def test_create_session(self, temp_jarvis_dir):
        from app.runtime.runtime_session import RuntimeSessionManager

        manager = RuntimeSessionManager()
        session = manager.create_session(
            project_name="hospital",
            goal="Build Hospital Management System",
            tasks=["architect", "backend", "frontend", "testing"],
        )

        assert session.session_id.startswith("session-")
        assert session.project_name == "hospital"
        assert session.status == "pending"
        assert len(session.pending_tasks) == 4
        assert session.started_at is not None

    def test_session_persistence(self, temp_jarvis_dir):
        from app.runtime.runtime_session import RuntimeSessionManager

        manager = RuntimeSessionManager()
        session = manager.create_session(
            project_name="hospital",
            goal="Build Hospital Management System",
            tasks=["architect", "backend"],
        )

        # Load from disk
        loaded = manager.get_session(session.session_id)
        assert loaded is not None
        assert loaded.session_id == session.session_id
        assert loaded.project_name == "hospital"

    def test_session_progress(self, temp_jarvis_dir):
        from app.runtime.runtime_session import RuntimeSessionManager

        manager = RuntimeSessionManager()
        session = manager.create_session(
            project_name="hospital",
            goal="Build Hospital Management System",
            tasks=["architect", "backend", "frontend"],
        )

        manager.start_phase(session.session_id, "architect")
        manager.complete_task(session.session_id, "architect")

        progress = manager.get_progress(session.session_id)
        assert progress["completed"] == 1
        assert progress["pending"] == 2
        assert progress["progress_percent"] == 33.3


class TestCheckpointManager:
    """Test checkpoint creation and recovery."""

    def test_create_checkpoint(self, temp_jarvis_dir):
        from app.runtime.checkpoint_manager import CheckpointManager

        manager = CheckpointManager()
        checkpoint_id = manager.create_checkpoint(
            session_id="session-test123",
            project_name="hospital",
            goal="Build Hospital Management System",
            phase="backend",
            completed_tasks=["architect"],
            pending_tasks=["frontend", "testing"],
        )

        assert checkpoint_id.startswith("ckpt-")

        # Load the checkpoint to verify
        checkpoint = manager.load(checkpoint_id)
        assert checkpoint is not None
        assert checkpoint.phase == "backend"
        assert checkpoint.completed_tasks == ["architect"]

    def test_latest_checkpoint(self, temp_jarvis_dir):
        from app.runtime.checkpoint_manager import CheckpointManager

        manager = CheckpointManager()

        manager.create_checkpoint(
            session_id="session-test123",
            project_name="hospital",
            goal="Build Hospital Management System",
            phase="architect",
            completed_tasks=[],
            pending_tasks=["backend", "frontend"],
        )

        manager.create_checkpoint(
            session_id="session-test123",
            project_name="hospital",
            goal="Build Hospital Management System",
            phase="backend",
            completed_tasks=["architect"],
            pending_tasks=["frontend"],
        )

        latest = manager.latest("session-test123")
        assert latest is not None
        assert latest.phase == "backend"

    def test_can_resume(self, temp_jarvis_dir):
        from app.runtime.checkpoint_manager import CheckpointManager

        manager = CheckpointManager()
        assert manager.can_resume("session-nonexistent") is False

        manager.create_checkpoint(
            session_id="session-test123",
            project_name="hospital",
            goal="Build Hospital Management System",
            phase="architect",
            completed_tasks=[],
            pending_tasks=["backend"],
        )

        assert manager.can_resume("session-test123") is True


class TestArtifactManager:
    """Test artifact management."""

    def test_add_artifact(self, temp_jarvis_dir):
        from app.runtime.artifact_manager import ArtifactManager

        manager = ArtifactManager()
        artifact = manager.add(
            name="main.py",
            artifact_type="code",
            content="print('hello')",
            created_by="backend_agent",
            tags=["python", "entry-point"],
        )

        assert artifact.artifact_id is not None
        assert artifact.name == "main.py"
        assert artifact.artifact_type == "code"
        assert artifact.checksum != ""

    def test_list_artifacts_by_type(self, temp_jarvis_dir):
        from app.runtime.artifact_manager import ArtifactManager

        manager = ArtifactManager()
        manager.add(name="main.py", artifact_type="code", content="code1")
        manager.add(name="README.md", artifact_type="docs", content="docs1")
        manager.add(name="test.py", artifact_type="code", content="code2")

        code_artifacts = manager.get_by_type("code")
        assert len(code_artifacts) == 2


class TestProgressTracker:
    """Test progress tracking."""

    def test_task_lifecycle(self, temp_jarvis_dir):
        from app.runtime.progress_tracker import ProgressTracker, TaskState

        tracker = ProgressTracker()
        tracker.register_task("backend", "Backend Development", agent="backend_agent")

        task = tracker.get("backend")
        assert task.state == TaskState.PENDING

        tracker.start("backend")
        task = tracker.get("backend")
        assert task.state == TaskState.RUNNING
        assert task.attempts == 1

        tracker.complete("backend", output="Backend complete")
        task = tracker.get("backend")
        assert task.state == TaskState.COMPLETED

    def test_progress_summary(self, temp_jarvis_dir):
        from app.runtime.progress_tracker import ProgressTracker

        tracker = ProgressTracker()
        tracker.register_task("architect", "Architecture")
        tracker.register_task("backend", "Backend")
        tracker.register_task("frontend", "Frontend")

        tracker.start("architect")
        tracker.complete("architect")
        tracker.start("backend")

        summary = tracker.summary()
        assert summary["total"] == 3
        assert summary["completed"] == 1
        assert summary["running"] == 1
        assert summary["pending"] == 1


class TestRetryManager:
    """Test retry management."""

    def test_successful_execution(self, temp_jarvis_dir):
        from app.runtime.retry_manager import RetryManager, RetryPolicy

        manager = RetryManager(RetryPolicy(max_retries=3))
        result = manager.execute_with_retry(
            task_name="test_task",
            handler=lambda: "success",
        )

        assert result.success is True
        assert result.attempts == 1

    def test_retry_with_repair(self, temp_jarvis_dir):
        from app.runtime.retry_manager import RetryManager, RetryPolicy

        manager = RetryManager(RetryPolicy(max_retries=3))
        attempts = {"count": 0}

        def failing_then_succeed():
            attempts["count"] += 1
            if attempts["count"] < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = manager.execute_with_retry(
            task_name="test_task",
            handler=failing_then_succeed,
            repair_handler=lambda err: None,
        )

        assert result.success is True
        assert result.attempts == 2

    def test_max_retries_exceeded(self, temp_jarvis_dir):
        from app.runtime.retry_manager import RetryManager, RetryPolicy

        manager = RetryManager(RetryPolicy(max_retries=2))

        def always_fail():
            raise RuntimeError("Permanent failure")

        result = manager.execute_with_retry(
            task_name="test_task",
            handler=always_fail,
        )

        assert result.success is False
        assert result.attempts == 2  # max_retries=2 means 2 total attempts
        assert "Permanent failure" in result.last_error


class TestRuntimeEvents:
    """Test runtime event system."""

    def test_publish_event(self, temp_jarvis_dir):
        from app.runtime.runtime_events import RuntimeEventBus

        bus = RuntimeEventBus()
        event = bus.publish(
            event_type="PROJECT_STARTED",
            session_id="session-test",
            message="Project started",
        )

        assert event.event_type == "PROJECT_STARTED"
        assert event.session_id == "session-test"

    def test_event_history(self, temp_jarvis_dir):
        from app.runtime.runtime_events import RuntimeEventBus

        bus = RuntimeEventBus()
        bus.publish(event_type="PROJECT_STARTED", session_id="session-test")
        bus.publish(event_type="PHASE_COMPLETED", session_id="session-test", phase="backend")
        bus.publish(event_type="PROJECT_STARTED", session_id="session-other")

        events = bus.history(session_id="session-test")
        assert len(events) == 2

    def test_event_subscription(self, temp_jarvis_dir):
        from app.runtime.runtime_events import RuntimeEventBus, RuntimeEvent

        bus = RuntimeEventBus()
        received_events = []

        def handler(event: RuntimeEvent):
            received_events.append(event)

        bus.subscribe(handler)
        bus.publish(event_type="TEST_EVENT", message="test")

        assert len(received_events) == 1
        assert received_events[0].event_type == "TEST_EVENT"


class TestBenchmarkTracker:
    """Test benchmark tracking."""

    def test_record_benchmark(self, temp_jarvis_dir):
        from app.metrics.benchmark import BenchmarkTracker

        tracker = BenchmarkTracker()
        result = tracker.record_execution_time(120.5)

        assert result.name == "execution_time"
        assert result.value == 120.5
        assert result.unit == "seconds"

    def test_benchmark_comparison(self, temp_jarvis_dir):
        from app.metrics.benchmark import BenchmarkTracker

        tracker = BenchmarkTracker()
        tracker.record_execution_time(98.3)

        comp = tracker.compare_with_baseline("execution_time", 120.5)
        assert comp is not None
        assert comp.improved is True
        assert comp.delta_pct < 0

    def test_benchmark_summary(self, temp_jarvis_dir):
        from app.metrics.benchmark import BenchmarkTracker

        tracker = BenchmarkTracker()
        tracker.record_execution_time(120.5)
        tracker.record_memory_usage(256.0)
        tracker.record_llm_calls(145)

        summary = tracker.summary()
        assert summary["total_benchmarks"] == 3


class TestCodeMetrics:
    """Test code metrics analysis."""

    def test_analyze_python_file(self, temp_jarvis_dir):
        from app.metrics.code_metrics import CodeMetricsAnalyzer

        analyzer = CodeMetricsAnalyzer()
        content = '''"""Module docstring."""

import os
import sys


def hello():
    """Say hello."""
    print("hello")


class Greeter:
    """A greeter class."""

    def __init__(self):
        self.name = "world"

    def greet(self):
        """Greet someone."""
        if self.name:
            print(f"Hello, {self.name}")
'''

        metrics = analyzer.analyze_file("greeter.py", content)
        assert metrics.functions == 3
        assert metrics.classes == 1
        assert metrics.imports == 2
        assert metrics.lines > 0

    def test_analyze_project(self, temp_jarvis_dir):
        from app.metrics.code_metrics import CodeMetricsAnalyzer

        analyzer = CodeMetricsAnalyzer()
        files = {
            "main.py": "def main():\n    pass\n",
            "utils.py": "def helper():\n    return True\n",
        }

        report = analyzer.analyze_project(files)
        assert report.files_count == 2
        assert report.total_functions == 2


class TestPerformanceMetrics:
    """Test performance tracking."""

    def test_phase_timing(self, temp_jarvis_dir):
        from app.metrics.performance_metrics import PerformanceTracker

        tracker = PerformanceTracker()
        tracker.start_phase("backend")
        time.sleep(0.01)
        phase = tracker.end_phase("backend")

        assert phase.phase == "backend"
        assert phase.duration > 0

    def test_performance_report(self, temp_jarvis_dir):
        from app.metrics.performance_metrics import PerformanceTracker

        tracker = PerformanceTracker()
        tracker.start_phase("architect")
        time.sleep(0.01)
        tracker.end_phase("architect")

        tracker.start_phase("backend")
        time.sleep(0.01)
        tracker.end_phase("backend")

        report = tracker.generate_report()
        assert report.total_duration > 0
        assert len(report.phases) == 2


class TestQualityMetrics:
    """Test quality metrics calculation."""

    def test_calculate_quality(self, temp_jarvis_dir):
        from app.metrics.quality_metrics import QualityMetricsEngine

        engine = QualityMetricsEngine()
        report = engine.calculate_quality(
            project_name="hospital",
            code_metrics={
                "avg_complexity": 4.2,
                "duplication_estimate": 0.05,
                "avg_function_length": 15.0,
                "documentation_ratio": 0.25,
            },
            test_results={
                "total_tests": 142,
                "passed": 140,
                "failed": 2,
                "coverage_percent": 96.0,
            },
            security_results={
                "vulnerabilities": 1,
                "critical": 0,
                "warnings": 3,
            },
            architecture_score=97.0,
        )

        assert report.overall_score > 0
        assert report.grade in ("A", "B", "C", "D", "F")
        assert len(report.dimensions) >= 5

    def test_quality_grade(self, temp_jarvis_dir):
        from app.metrics.quality_metrics import QualityMetricsEngine

        engine = QualityMetricsEngine()

        assert engine._score_to_grade(95) == "A"
        assert engine._score_to_grade(85) == "B"
        assert engine._score_to_grade(75) == "C"
        assert engine._score_to_grade(65) == "D"
        assert engine._score_to_grade(50) == "F"


class TestLearningEngine:
    """Test learning engine integration."""

    def test_learn_from_execution(self, temp_jarvis_dir):
        from app.learning.learning_engine import LearningEngine

        engine = LearningEngine()
        result = engine.learn({
            "goal": "Build Hospital Management System",
            "success": True,
            "duration": 120.5,
            "artifacts": 15,
            "errors": 2,
        }, success=True)

        assert result["success"] is True

    def test_recall_similar(self, temp_jarvis_dir):
        from app.learning.learning_engine import LearningEngine

        engine = LearningEngine()
        engine.learn({
            "goal": "Build Hospital Management System",
            "success": True,
        }, success=True)

        similar = engine.recall("hospital")
        assert isinstance(similar, list)


class TestProjectHistory:
    """Test project history tracking."""

    def test_record_execution(self, temp_jarvis_dir):
        from app.learning.project_history import ProjectHistory

        history = ProjectHistory()
        entry = history.record_execution(
            project_name="hospital",
            goal="Build Hospital Management System",
            status="completed",
            duration=120.5,
            overall_score=95.8,
            files_generated=182,
            tests_count=142,
            repair_count=2,
        )

        assert entry.project_name == "hospital"
        assert entry.status == "completed"

    def test_find_similar_projects(self, temp_jarvis_dir):
        from app.learning.project_history import ProjectHistory

        history = ProjectHistory()
        history.record_execution(
            project_name="hospital",
            goal="Build Hospital Management System",
            status="completed",
            duration=120.5,
        )
        history.record_execution(
            project_name="clinic",
            goal="Build Clinic Management System",
            status="completed",
            duration=98.3,
        )

        similar = history.find_similar("hospital management")
        assert len(similar) >= 1


class TestImprovementEngine:
    """Test improvement comparison engine."""

    def test_compare_versions(self, temp_jarvis_dir):
        from app.learning.improvement_engine import ImprovementEngine

        engine = ImprovementEngine()
        baseline = {
            "duration": 120.5,
            "files_generated": 150,
            "repair_count": 5,
            "overall_score": 88.0,
            "coverage": 91.0,
        }
        current = {
            "duration": 98.3,
            "files_generated": 182,
            "repair_count": 3,
            "overall_score": 95.8,
            "coverage": 96.0,
        }

        result = engine.compare(baseline, current)
        assert "deltas" in result
        assert "notes" in result

    def test_improvement_detection(self, temp_jarvis_dir):
        from app.learning.improvement_engine import ImprovementEngine

        engine = ImprovementEngine()
        baseline = {"duration": 100.0, "repair_count": 10}
        current = {"duration": 82.0, "repair_count": 6}

        result = engine.compare(baseline, current)
        notes = result["notes"]

        assert any("Runtime improved" in n for n in notes)
        assert any("Repairs reduced" in n for n in notes)


class TestEndToEndFlow:
    """Test the complete Sprint 9 execution flow."""

    def test_full_execution_flow(self, temp_jarvis_dir):
        """Simulate a complete project execution with all modules."""
        from app.runtime.runtime_session import RuntimeSessionManager
        from app.runtime.checkpoint_manager import CheckpointManager
        from app.runtime.artifact_manager import ArtifactManager
        from app.runtime.progress_tracker import ProgressTracker
        from app.runtime.retry_manager import RetryManager, RetryPolicy
        from app.runtime.runtime_events import RuntimeEventBus
        from app.metrics.benchmark import BenchmarkTracker
        from app.metrics.code_metrics import CodeMetricsAnalyzer
        from app.metrics.performance_metrics import PerformanceTracker
        from app.metrics.quality_metrics import QualityMetricsEngine
        from app.learning.project_history import ProjectHistory
        from app.learning.improvement_engine import ImprovementEngine

        # Initialize all components
        sessions = RuntimeSessionManager()
        checkpoints = CheckpointManager()
        artifacts = ArtifactManager()
        progress = ProgressTracker()
        retry = RetryManager(RetryPolicy(max_retries=3))
        events = RuntimeEventBus()
        benchmarks = BenchmarkTracker()
        code_analyzer = CodeMetricsAnalyzer()
        perf_tracker = PerformanceTracker()
        quality_engine = QualityMetricsEngine()
        history = ProjectHistory()
        improvement = ImprovementEngine()

        # Track events
        event_log = []
        events.subscribe(lambda e: event_log.append(e.event_type))

        # Step 1: Create session
        session = sessions.create_session(
            project_name="hospital",
            goal="Build Hospital Management System",
            tasks=["architect", "backend", "database", "frontend", "testing", "deployment"],
        )
        events.publish("PROJECT_STARTED", session_id=session.session_id)

        # Step 2: Execute phases with checkpoints
        phases = ["architect", "backend", "database", "frontend", "testing", "deployment"]
        completed_phases = []
        for phase in phases:
            sessions.start_phase(session.session_id, phase)
            progress.register_task(phase, phase.replace("_", " ").title())
            progress.start(phase)
            events.publish("PHASE_STARTED", session_id=session.session_id, phase=phase)

            perf_tracker.start_phase(phase)

            # Simulate work
            def phase_work():
                time.sleep(0.001)
                return f"{phase} complete"

            result = retry.execute_with_retry(
                task_name=phase,
                handler=phase_work,
            )

            perf_tracker.end_phase(phase)

            if result.success:
                progress.complete(phase)
                sessions.complete_task(session.session_id, phase)
                completed_phases.append(phase)
                events.publish("PHASE_COMPLETED", session_id=session.session_id, phase=phase)
            else:
                progress.fail(phase, result.last_error)
                events.publish("PHASE_FAILED", session_id=session.session_id, phase=phase)

            # Create checkpoint after each phase
            checkpoints.create_checkpoint(
                session_id=session.session_id,
                project_name=session.project_name,
                goal=session.goal,
                phase=phase,
                completed_tasks=list(completed_phases),
                pending_tasks=[p for p in phases if p not in completed_phases],
            )

        # Step 3: Add artifacts
        artifacts.add("main.py", "code", "def main(): pass", created_by="backend")
        artifacts.add("README.md", "docs", "# Hospital System", created_by="docs")
        artifacts.add("Dockerfile", "config", "FROM python:3.11", created_by="devops")

        # Step 4: Record benchmarks
        benchmarks.record_execution_time(perf_tracker.generate_report().total_duration)
        benchmarks.record_memory_usage(256.0)
        benchmarks.record_llm_calls(145)

        # Step 5: Analyze code
        code_report = code_analyzer.analyze_project({
            "main.py": "def main():\n    pass\n",
            "models.py": "class Patient:\n    pass\n",
        })

        # Step 6: Calculate quality
        quality_report = quality_engine.calculate_quality(
            project_name="hospital",
            code_metrics={
                "avg_complexity": code_report.avg_complexity,
                "duplication_estimate": code_report.duplication_estimate,
                "avg_function_length": code_report.avg_function_length,
                "documentation_ratio": code_report.documentation_ratio,
            },
            test_results={
                "total_tests": 142,
                "passed": 140,
                "failed": 2,
                "coverage_percent": 96.0,
            },
            architecture_score=97.0,
        )

        # Step 7: Record in history
        history.record_execution(
            project_name="hospital",
            goal="Build Hospital Management System",
            status="completed",
            duration=perf_tracker.generate_report().total_duration,
            overall_score=quality_report.overall_score,
            files_generated=code_report.files_count,
            tests_count=142,
            repair_count=2,
        )

        # Step 8: Verify everything worked
        assert len(event_log) > 0
        assert "PROJECT_STARTED" in event_log
        assert "PHASE_COMPLETED" in event_log

        # Verify checkpoints
        assert checkpoints.can_resume(session.session_id)
        latest_checkpoint = checkpoints.latest(session.session_id)
        assert latest_checkpoint.phase == "deployment"

        # Verify progress
        progress_summary = progress.summary()
        assert progress_summary["completed"] == 6

        # Verify artifacts
        assert len(artifacts.get_by_type("code")) >= 1

        # Verify quality
        assert quality_report.overall_score > 0
        assert quality_report.grade in ("A", "B", "C", "D", "F")

    def test_crash_recovery(self, temp_jarvis_dir):
        """Test that execution can resume after a crash at 70%."""
        from app.runtime.runtime_session import RuntimeSessionManager
        from app.runtime.checkpoint_manager import CheckpointManager
        from app.runtime.progress_tracker import ProgressTracker
        from app.runtime.runtime_events import RuntimeEventBus

        sessions = RuntimeSessionManager()
        checkpoints = CheckpointManager()
        progress = ProgressTracker()
        events = RuntimeEventBus()

        # Simulate first run that crashes at 70%
        session = sessions.create_session(
            project_name="hospital",
            goal="Build Hospital Management System",
            tasks=["architect", "backend", "database", "frontend", "testing", "deployment"],
        )

        # Complete ~70% of phases (4 out of 6)
        completed_phases = ["architect", "backend", "database", "frontend"]
        for phase in completed_phases:
            sessions.start_phase(session.session_id, phase)
            progress.register_task(phase, phase.title())
            progress.start(phase)
            progress.complete(phase)
            sessions.complete_task(session.session_id, phase)

            checkpoints.create_checkpoint(
                session_id=session.session_id,
                project_name=session.project_name,
                goal=session.goal,
                phase=phase,
                completed_tasks=completed_phases[:completed_phases.index(phase) + 1],
                pending_tasks=["testing", "deployment"],
            )

        # Simulate crash - create new instances (like restarting Jarvis)
        sessions2 = RuntimeSessionManager()
        checkpoints2 = CheckpointManager()

        # Verify recovery is possible
        assert checkpoints2.can_resume(session.session_id)

        # Get last checkpoint
        last_checkpoint = checkpoints2.latest(session.session_id)
        assert last_checkpoint is not None
        assert last_checkpoint.phase == "frontend"

        # Resume from checkpoint
        resumed_session = sessions2.get_session(session.session_id)
        assert resumed_session is not None

        # Verify completed phases are preserved
        progress_data = sessions2.get_progress(session.session_id)
        assert progress_data["completed"] == 4

        # Continue with remaining phases
        remaining_phases = ["testing", "deployment"]
        for phase in remaining_phases:
            sessions2.start_phase(session.session_id, phase)
            progress.start(phase)
            progress.complete(phase)
            sessions2.complete_task(session.session_id, phase)

        # Verify all phases completed
        final_progress = sessions2.get_progress(session.session_id)
        assert final_progress["completed"] == 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
