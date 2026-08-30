"""Autonomous Project Execution Runtime (APER).

Orchestrates the full engineering lifecycle:
  - Workspace management
  - Task scheduling with dependencies
  - Live progress tracking
  - Artifact persistence
  - Incremental builds
  - Project diffing
  - Report generation
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

from app.agents.agent_orchestrator import AgentOrchestrator
from app.agents.project_context import ProjectContext
from app.core.logger import Logger
from app.core.results import ExecutionResult
from app.engineering.engineering_pipeline import EngineeringPipeline
from app.engineering.engineering_agent import EngineeringAgent
from app.events.event_bus import EventBus
from app.runtime.artifact_manager import ArtifactManager
from app.runtime.build_state import BuildStateManager
from app.runtime.progress_tracker import ProgressTracker, TaskState
from app.runtime.project_diff import ProjectDiffEngine
from app.runtime.report_generator import EngineeringReport, ReportGenerator
from app.runtime.workspace import EngineeringWorkspace


class ExecutionRuntime:
    """Main runtime for autonomous project execution."""

    def __init__(
        self,
        workspace: Optional[EngineeringWorkspace] = None,
        pipeline: Optional[EngineeringPipeline] = None,
        agent_orchestrator: Optional[AgentOrchestrator] = None,
        event_bus: Optional[EventBus] = None,
    ):
        self.workspace = workspace
        self.pipeline = pipeline or EngineeringPipeline()
        self.agent_orchestrator = agent_orchestrator or AgentOrchestrator()
        self.event_bus = event_bus or EventBus()
        self.progress: Optional[ProgressTracker] = None
        self.artifacts: Optional[ArtifactManager] = None
        self.build_state: Optional[BuildStateManager] = None
        self.reports: Optional[ReportGenerator] = None

    def initialize(self, workspace: EngineeringWorkspace) -> ExecutionResult:
        """Initialize the runtime with a workspace."""
        self.workspace = workspace
        workspace.initialize()
        
        self.progress = ProgressTracker(workspace.progress_json)
        self.artifacts = ArtifactManager(workspace.artifacts_dir)
        self.build_state = BuildStateManager(os.path.join(workspace.state_dir, "build_state.json"))
        self.reports = ReportGenerator(workspace.reports_dir)
        
        Logger.info(f"[ExecutionRuntime] Initialized workspace: {workspace.root}")
        return ExecutionResult.completed(message="Runtime initialized", artifacts=[workspace.root])

    def run(self, goal: str, incremental: bool = True) -> ExecutionResult:
        """Run the full engineering pipeline for a goal."""
        if not self.workspace:
            return ExecutionResult.failed("Runtime not initialized. Call initialize() first.")
        
        started = time.perf_counter()
        self.workspace.goal = goal
        self.workspace.status = "running"
        self._save_workspace()
        
        # Register core tasks
        self.progress.register_task("ceo", "CEO Orchestration", agent="ceo", max_retries=1)
        self.progress.register_task("requirement", "Requirement Analysis", agent="requirement", max_retries=2)
        self.progress.register_task("architect", "Architecture Design", agent="architect", max_retries=2)
        self.progress.register_task("backend", "Backend Generation", agent="backend", max_retries=3)
        self.progress.register_task("frontend", "Frontend Generation", agent="frontend", max_retries=2)
        self.progress.register_task("database", "Database Design", agent="database", max_retries=2)
        self.progress.register_task("tester", "Testing", agent="tester", max_retries=2)
        self.progress.register_task("security", "Security Scan", agent="security", max_retries=1)
        self.progress.register_task("deployment", "Deployment Config", agent="deployment", max_retries=1)
        self.progress.register_task("reviewer", "Review", agent="reviewer", max_retries=1)
        self.progress.register_task("documentation", "Documentation", agent="documentation", max_retries=1)
        
        # Run agent orchestrator
        Logger.info(f"[ExecutionRuntime] Starting pipeline for: {goal}")
        self.event_bus.publish("PROJECT_STARTED", {"goal": goal, "workspace": self.workspace.root})
        
        try:
            result = self.agent_orchestrator.run(goal)
        except Exception as exc:
            self.workspace.status = "failed"
            self._save_workspace()
            return ExecutionResult.failed(str(exc), duration=time.perf_counter() - started)
        
        duration = time.perf_counter() - started
        self.workspace.status = "completed" if result.success else "completed_with_errors"
        self.workspace.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        self._save_workspace()
        
        # Generate report
        report = self._build_report(goal, result, duration)
        report_paths = self.reports.generate(report)
        
        # Persist artifacts
        self.artifacts.add("execution_result", "report", result.to_dict(), created_by="execution_runtime")
        self.artifacts.add("progress", "state", self.progress.summary(), created_by="execution_runtime")
        
        self.event_bus.publish("PROJECT_FINISHED", {"success": result.success, "duration": duration})
        
        message = f"Project execution completed in {duration:.2f}s"
        if result.errors:
            message += f" with {len(result.errors)} errors"
        
        return ExecutionResult(
            success=result.success,
            status="completed" if result.success else "completed_with_errors",
            message=message,
            data=result.data,
            metrics=result.metrics,
            warnings=result.warnings,
            errors=result.errors,
            artifacts=[self.workspace.root] + list(report_paths.values()),
            duration=duration,
        )

    def run_incremental(self, goal: str) -> ExecutionResult:
        """Run an incremental build, modifying existing project."""
        if not self.workspace:
            return ExecutionResult.failed("Runtime not initialized.")
        
        # Load existing build state
        changed_files = self.build_state.get_changed_files({})
        new_files = self.build_state.get_new_files({})
        
        Logger.info(f"[ExecutionRuntime] Incremental build: {len(changed_files)} changed, {len(new_files)} new")
        
        # For incremental builds, we still run the full pipeline but only
        # regenerate changed/new files. The project builder handles this.
        result = self.run(goal, incremental=True)
        
        if result.success and self.workspace.project_path:
            # Record all generated files in build state
            for root, _, files in os.walk(self.workspace.project_path):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    rel_path = os.path.relpath(filepath, self.workspace.project_path)
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                            content = f.read()
                        self.build_state.record_file(rel_path, content, generated_by="incremental_build")
                    except (OSError, UnicodeDecodeError):
                        pass
            self.build_state.record_build(goal)
        
        return result

    def diff_versions(self, old_path: str, new_path: str) -> ExecutionResult:
        """Compare two project versions."""
        if not os.path.isdir(old_path) or not os.path.isdir(new_path):
            return ExecutionResult.failed("Invalid paths for diff")
        
        engine = ProjectDiffEngine(old_path, new_path)
        diff = engine.compute()
        
        return ExecutionResult.completed(
            data=diff.to_dict(),
            message=f"Diff complete: {diff.summary.get('total_changed', 0)} changes",
            metrics=diff.summary,
        )

    def generate_report(self, report: EngineeringReport) -> ExecutionResult:
        """Generate engineering report."""
        if not self.reports:
            return ExecutionResult.failed("Report generator not initialized.")
        
        paths = self.reports.generate(report)
        return ExecutionResult.completed(
            data={"paths": paths, "report": report.to_dict()},
            message="Report generated",
            artifacts=list(paths.values()),
        )

    def _build_report(self, goal: str, result: ExecutionResult, duration: float) -> EngineeringReport:
        """Build a report from execution results."""
        ctx = result.data if isinstance(result.data, dict) else {}
        benchmark = ctx.get("benchmark", {}) if isinstance(ctx, dict) else {}
        
        report = EngineeringReport(
            project_name=ctx.get("project_name", "") if isinstance(ctx, dict) else "",
            goal=goal,
            status=self.workspace.status if self.workspace else "unknown",
            duration_seconds=duration,
            requirements=ctx.get("requirements", {}) if isinstance(ctx, dict) else {},
            architecture=ctx.get("architecture", {}) if isinstance(ctx, dict) else {},
            files_generated=ctx.get("files", []) if isinstance(ctx, dict) else [],
            benchmark=benchmark,
            overall_score=benchmark.get("overall_score", 0.0) if isinstance(benchmark, dict) else 0.0,
            known_issues=list(result.errors) if result.errors else [],
            llm_usage=result.metrics.get("llm_usage", {}) if isinstance(result.metrics, dict) else {},
        )
        return report

    def _save_workspace(self):
        if self.workspace:
            workspace_data = self.workspace.to_dict()
            try:
                with open(self.workspace.project_json, "w", encoding="utf-8") as f:
                    json.dump(workspace_data, f, indent=2, default=str)
            except (OSError, TypeError):
                pass

    execute = run
