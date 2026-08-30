"""Project runtime - high-level orchestrator for autonomous project execution.

This is the main entry point that:
  1. Creates a runtime session
  2. Runs the agent pipeline
  3. Saves checkpoints after each phase
  4. Handles crashes and resumes from checkpoints
  5. Generates final reports
  6. Feeds metrics and learning engines
"""

from __future__ import annotations

import os
import time
from typing import Any, Callable, Dict, List, Optional

from app.core.logger import Logger
from app.runtime.runtime_events import RuntimeEventBus
from app.runtime.runtime_session import RuntimeSession, RuntimeSessionManager
from app.runtime.checkpoint_manager import CheckpointManager, Checkpoint
from app.runtime.artifact_manager import ArtifactManager
from app.runtime.progress_tracker import ProgressTracker, TaskState
from app.runtime.retry_manager import RetryManager, RetryPolicy, RetryResult
from app.runtime.snapshot_store import SnapshotStore
from app.metrics.metrics_engine import MetricsEngine
from app.learning.learning_engine import LearningEngine


class ProjectRuntime:
    """Autonomous project runtime.

    Wraps the orchestrator with crash recovery, metrics, and learning.
    """

    def __init__(
        self,
        session_manager: Optional[RuntimeSessionManager] = None,
        checkpoint_manager: Optional[CheckpointManager] = None,
        artifact_manager: Optional[ArtifactManager] = None,
        progress_tracker: Optional[ProgressTracker] = None,
        retry_manager: Optional[RetryManager] = None,
        event_bus: Optional[RuntimeEventBus] = None,
        metrics_engine: Optional[MetricsEngine] = None,
        learning_engine: Optional[LearningEngine] = None,
        orchestrator: Optional[Any] = None,
    ):
        self.sessions = session_manager or RuntimeSessionManager()
        self.checkpoints = checkpoint_manager or CheckpointManager()
        self.artifacts = artifact_manager or ArtifactManager()
        self.progress = progress_tracker or ProgressTracker()
        self.retry = retry_manager or RetryManager()
        self.events = event_bus or RuntimeEventBus()
        self.metrics = metrics_engine or MetricsEngine()
        self.learning = learning_engine or LearningEngine()
        self.orchestrator = orchestrator
        self.snapshots = SnapshotStore()

    def run(self, requirement: str, resume_session_id: Optional[str] = None) -> Dict[str, Any]:
        """Run a project from start or resume from checkpoint.

        Flow:
          - If resume_session_id: load checkpoint, resume
          - Else: create new session, run full pipeline
        """
        started = time.perf_counter()

        if resume_session_id:
            return self._resume(requirement, resume_session_id, started)

        return self._start_new(requirement, started)

    def _start_new(self, requirement: str, started: float) -> Dict[str, Any]:
        """Start a new project execution."""
        session = self.sessions.create_session(
            project_name=self._project_name_from(requirement),
            goal=requirement,
            tasks=self._default_tasks(),
        )

        self.events.publish("PROJECT_STARTED", session_id=session.session_id,
                            message=f"Starting: {requirement}")

        try:
            result = self._execute_pipeline(session, requirement)
        except Exception as exc:
            self._handle_failure(session, str(exc))
            raise

        duration = time.perf_counter() - started
        self._finalize(session, result, duration)
        return result

    def _resume(self, requirement: str, session_id: str, started: float) -> Dict[str, Any]:
        """Resume from a checkpoint."""
        checkpoint = self.checkpoints.latest(session_id)
        if not checkpoint:
            raise ValueError(f"No checkpoint found for session: {session_id}")

        session = self.sessions.get_session(session_id)
        if not session:
            raise ValueError(f"No session found: {session_id}")

        session.status = "resumed"
        session.current_phase = checkpoint.phase
        session.completed_tasks = list(checkpoint.completed_tasks)
        session.pending_tasks = list(checkpoint.pending_tasks)
        self.sessions.update_status(session_id, "running")

        self.events.publish("PROJECT_RESUMED", session_id=session_id,
                            phase=checkpoint.phase,
                            message=f"Resumed from {checkpoint.phase}")

        try:
            result = self._execute_pipeline(session, requirement, resume_from=checkpoint.phase)
        except Exception as exc:
            self._handle_failure(session, str(exc))
            raise

        duration = time.perf_counter() - started
        self._finalize(session, result, duration)
        return result

    def _execute_pipeline(self, session: RuntimeSession, requirement: str,
                          resume_from: Optional[str] = None) -> Dict[str, Any]:
        """Execute the agent pipeline with checkpoints and retries."""
        phases = self._phases()
        if resume_from:
            phases = phases[phases.index(resume_from):]

        result: Dict[str, Any] = {"success": True, "session_id": session.session_id}

        for phase in phases:
            session.current_phase = phase
            self.sessions.start_phase(session.session_id, phase)
            self.events.publish("PHASE_STARTED", session_id=session.session_id,
                                phase=phase, message=f"Phase started: {phase}")

            task_id = self._task_for_phase(phase)
            self.progress.start(task_id)

            handler = self._handler_for_phase(phase, requirement, session)
            retry_result = self.retry.execute_with_retry(
                task_name=task_id,
                handler=handler,
                repair_handler=lambda err: self._repair(phase, session, err),
            )
            self.retry.record(task_id, retry_result)

            if retry_result.success:
                self.progress.complete(task_id, output=str(retry_result.output))
                self.events.publish("PHASE_COMPLETED", session_id=session.session_id,
                                    phase=phase, message=f"Phase completed: {phase}")
            else:
                self.progress.fail(task_id, retry_result.last_error)
                self.events.publish("PHASE_FAILED", session_id=session.session_id,
                                    phase=phase, message=f"Phase failed: {phase}")
                result["success"] = False
                result["error"] = retry_result.last_error

            self.sessions.complete_task(session.session_id, task_id)
            self.checkpoints.create_checkpoint(
                session_id=session.session_id,
                project_name=session.project_name,
                goal=session.goal,
                phase=phase,
                completed_tasks=session.completed_tasks,
                pending_tasks=session.pending_tasks,
                artifacts=session.artifacts,
                errors=session.errors,
                logs=session.logs,
            )

        return result

    def _finalize(self, session: RuntimeSession, result: Dict[str, Any], duration: float):
        """Finalize execution: metrics, learning, report."""
        self.sessions.update_status(session.session_id, "completed" if result.get("success") else "failed")

        self.events.publish("PROJECT_FINISHED", session_id=session.session_id,
                            message=f"Project finished in {duration:.2f}s",
                            data={"success": result.get("success", False), "duration": duration})

        self.metrics.start_execution(session.goal, session.project_name)
        self.metrics.end_execution(success=result.get("success", False))

        self.learning.learn({
            "goal": session.goal,
            "success": result.get("success", False),
            "duration": duration,
            "artifacts": len(session.artifacts),
            "errors": len(session.errors),
        }, success=result.get("success", False))

    def _handle_failure(self, session: RuntimeSession, error: str):
        """Handle unexpected failure."""
        self.sessions.update_status(session.session_id, "failed")
        self.events.publish("PROJECT_FAILED", session_id=session.session_id, message=error)
        self.checkpoints.create_checkpoint(
            session_id=session.session_id,
            project_name=session.project_name,
            goal=session.goal,
            phase=session.current_phase,
            completed_tasks=session.completed_tasks,
            pending_tasks=session.pending_tasks,
            errors=session.errors + [error],
        )

    def _repair(self, phase: str, session: RuntimeSession, error: Any):
        """Attempt repair after a failure."""
        self.events.publish("REPAIR_STARTED", session_id=session.session_id,
                            phase=phase, message=f"Repairing {phase}")
        Logger.warning(f"[ProjectRuntime] Repairing {phase}: {error}")
        self.events.publish("REPAIR_SUCCESS", session_id=session.session_id,
                            phase=phase, message=f"Repair attempted for {phase}")

    def _default_tasks(self) -> List[str]:
        return ["ceo", "requirement", "architect", "backend", "frontend",
                "database", "tester", "repair", "documentation", "deployment", "reviewer"]

    def _phases(self) -> List[str]:
        return ["requirement", "architect", "backend", "database", "frontend",
                "tester", "repair", "documentation", "deployment", "reviewer"]

    def _task_for_phase(self, phase: str) -> str:
        mapping = {
            "requirement": "requirement",
            "architect": "architect",
            "backend": "backend",
            "database": "database",
            "frontend": "frontend",
            "tester": "tester",
            "repair": "repair",
            "documentation": "documentation",
            "deployment": "deployment",
            "reviewer": "reviewer",
        }
        return mapping.get(phase, phase)

    def _handler_for_phase(self, phase: str, requirement: str,
                           session: RuntimeSession) -> Callable[[], Any]:
        """Get the handler for a phase.

        If an orchestrator is attached, delegate to it. Otherwise, return a no-op.
        """
        if self.orchestrator is None:
            return lambda: None

        def handler() -> Any:
            return self.orchestrator.run(requirement)

        return handler

    def _project_name_from(self, requirement: str) -> str:
        words = requirement.strip().split()
        candidates = [w for w in words if len(w) > 3]
        return candidates[0].lower() if candidates else "project"
