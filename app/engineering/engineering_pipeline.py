"""Engineering pipeline master orchestrator.

Ties all engineering modules into a single pipeline that transforms a raw
user goal into a completed, benchmarked, and self-reviewed project.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from app.engineering.architecture_agent import ArchitectureAgent
from app.engineering.benchmark_engine import BenchmarkEngine
from app.engineering.engineering_memory import EngineeringMemory, ProjectMemory
from app.engineering.execution_engine import ExecutionEngine, ExecutionPolicy, ExecutionResultArtifact, RetryStrategy
from app.engineering.project_context import ProjectContext
from app.engineering.requirement_analyzer import RequirementAnalyzer
from app.engineering.self_review import SelfReviewAgent
from app.engineering.task_graph import TaskGraph
from app.engineering.workspace_manager import WorkspaceManager
from app.core.logger import Logger
from app.core.results import ExecutionResult
from app.project.project_builder import ProjectBuilder


class EngineeringPipeline:
    """Master orchestrator for the autonomous software engineering lifecycle."""

    def __init__(
        self,
        requirement_analyzer=None,
        architecture_agent=None,
        execution_engine=None,
        benchmark_engine=None,
        self_review_agent=None,
        workspace_manager=None,
        engineering_memory=None,
        project_builder=None,
    ):
        self.requirement_analyzer = requirement_analyzer or RequirementAnalyzer()
        self.architecture_agent = architecture_agent or ArchitectureAgent()
        self.execution_engine = execution_engine or ExecutionEngine()
        self.benchmark_engine = benchmark_engine or BenchmarkEngine()
        self.self_review_agent = self_review_agent or SelfReviewAgent()
        self.workspace_manager = workspace_manager or WorkspaceManager()
        self.engineering_memory = engineering_memory or EngineeringMemory()
        self.project_builder = project_builder or ProjectBuilder()

    def run(self, goal: str) -> ExecutionResult:
        """Run the full engineering pipeline for a user goal.

        Stages:
          1. Requirement Analysis
          2. Architecture Design
          3. Workspace Creation
          4. Task Graph Construction
          5. Execution (generate + validate + repair)
          6. Benchmark Evaluation
          7. Self Review
          8. Memory Persistence

        Returns:
            ExecutionResult containing the full pipeline outcome.
        """
        context = ProjectContext(goal=goal)
        started = time.perf_counter()

        Logger.info(f"[EngineeringPipeline] Starting pipeline for: {goal}")

        # ------------------------------------------------------------------
        # Stage 1: Requirement Analysis
        # ------------------------------------------------------------------
        context.current_stage = "requirement_analysis"
        req_result = self.requirement_analyzer.analyze(goal)
        if not req_result.success:
            return self._fail(context, "requirement_analysis", req_result.message, started)

        context.requirements = req_result.data
        context.warnings.extend(req_result.warnings)
        Logger.success(f"[EngineeringPipeline] Requirements analyzed: {req_result.metrics}")

        # Derive project name from requirements
        project_name = self._derive_project_name(context.requirements, goal)
        context.project_name = project_name

        # ------------------------------------------------------------------
        # Stage 2: Architecture Design
        # ------------------------------------------------------------------
        context.current_stage = "architecture_design"
        arch_result = self.architecture_agent.design(context.requirements)
        if not arch_result.success:
            return self._fail(context, "architecture_design", arch_result.message, started)

        context.architecture = arch_result.data
        context.warnings.extend(arch_result.warnings)
        Logger.success(f"[EngineeringPipeline] Architecture designed: {context.architecture.get('architecture', {}).get('pattern')}")

        # ------------------------------------------------------------------
        # Stage 3: Workspace Creation
        # ------------------------------------------------------------------
        context.current_stage = "workspace_creation"
        ws_result = self.workspace_manager.create_project(project_name, goal=goal)
        if not ws_result.success:
            return self._fail(context, "workspace_creation", ws_result.message, started)

        context.project_path = ws_result.data.get("path", "")
        context.add_artifact(context.project_path)
        Logger.success(f"[EngineeringPipeline] Workspace created: {context.project_path}")

        # ------------------------------------------------------------------
        # Stage 4: Task Graph Construction
        # ------------------------------------------------------------------
        context.current_stage = "task_graph_construction"
        graph = self._build_task_graph(context)
        context.task_graph = graph.to_dict()
        Logger.success(f"[EngineeringPipeline] Task graph built: {len(graph.nodes())} nodes")

        # ------------------------------------------------------------------
        # Stage 5: Execution
        # ------------------------------------------------------------------
        context.current_stage = "execution"
        exec_result = self._execute_pipeline(graph, context)
        if not exec_result.success:
            context.status = "failed"
            context.errors.extend(exec_result.errors)
            return self._finalize(context, started, success=False, message=exec_result.message)

        context.status = "completed"
        Logger.success("[EngineeringPipeline] Execution completed")

        # ------------------------------------------------------------------
        # Stage 6: Benchmark Evaluation
        # ------------------------------------------------------------------
        context.current_stage = "benchmark"
        bench_result = self.benchmark_engine.evaluate(context.project_path, context.requirements)
        context.benchmark = bench_result.data if bench_result.success else {}
        context.warnings.extend(bench_result.warnings)
        context.errors.extend(bench_result.errors)
        Logger.success(f"[EngineeringPipeline] Benchmark score: {context.benchmark.get('overall_score')}")

        # ------------------------------------------------------------------
        # Stage 7: Self Review
        # ------------------------------------------------------------------
        context.current_stage = "self_review"
        review_result = self.self_review_agent.review(context.project_path, context=context.to_dict())
        context.self_review = review_result.data if review_result.success else {}
        context.warnings.extend(review_result.warnings)
        Logger.success(f"[EngineeringPipeline] Self-review confidence: {context.self_review.get('confidence')}")

        # ------------------------------------------------------------------
        # Stage 8: Memory Persistence
        # ------------------------------------------------------------------
        context.current_stage = "memory_persistence"
        memory = ProjectMemory(
            project_name=project_name,
            goal=goal,
            architecture=context.architecture,
            benchmark=context.benchmark,
            success=True,
            success_rate=context.benchmark.get("overall_score", 0.0) / 100.0,
            artifacts=context.artifacts,
        )
        self.engineering_memory.add_memory(memory)
        context.memory = memory.to_dict()
        Logger.success("[EngineeringPipeline] Memory persisted")

        # ------------------------------------------------------------------
        # Finalize
        # ------------------------------------------------------------------
        context.current_stage = "complete"
        overall_score = context.benchmark.get("overall_score", 0.0)
        message = (
            f"Engineering pipeline completed successfully. "
            f"Project: {project_name}. Overall score: {overall_score}"
        )
        return self._finalize(context, started, success=True, message=message)

    def _build_task_graph(self, context: ProjectContext) -> TaskGraph:
        """Build a task graph from the execution plan and architecture."""
        plan = context.execution_plan or {}
        graph = TaskGraph.from_plan(plan)

        # Ensure core pipeline tasks exist
        core_tasks = [
            "generate_project",
            "validate_project",
            "run_project",
            "fix_errors",
            "generate_readme",
            "generate_docker",
            "benchmark_project",
            "self_review_project",
        ]
        existing_names = set(graph.nodes().keys())
        for task in core_tasks:
            if task not in existing_names:
                graph.add_node(task, payload={"action": task})

        # Link core tasks in order
        for i in range(len(core_tasks) - 1):
            graph.add_edge(core_tasks[i], core_tasks[i + 1])

        return graph

    def _execute_pipeline(self, graph: TaskGraph, context: ProjectContext) -> ExecutionResult:
        """Execute the task graph using the project builder as the primary handler."""

        def default_handler(node) -> ExecutionResultArtifact:
            action = node.payload.get("action", node.name)
            node_start = time.perf_counter()
            try:
                if action == "generate_project":
                    architecture_folders = context.architecture.get("folders", [])
                    base_path = self.project_builder.build(
                        context.goal,
                        project_name=context.project_name,
                        base_path=context.project_path,
                        folders=architecture_folders,
                    )
                    context.project_path = base_path
                    context.add_artifact(base_path)
                    return ExecutionResultArtifact(
                        node_name=node.name,
                        success=True,
                        output={"project_path": base_path},
                        duration=time.perf_counter() - node_start,
                    )

                elif action == "validate_project":
                    valid, message = self.project_builder.validator.validate(
                        self._project_dict(context), context.project_path
                    )
                    return ExecutionResultArtifact(
                        node_name=node.name,
                        success=valid,
                        output={"valid": valid, "message": message},
                        error=None if valid else message,
                        duration=time.perf_counter() - node_start,
                    )

                elif action == "run_project":
                    passed, output = self.project_builder.runner.run(context.project_path)
                    return ExecutionResultArtifact(
                        node_name=node.name,
                        success=passed,
                        output={"passed": passed, "output": output},
                        error=None if passed else output,
                        duration=time.perf_counter() - node_start,
                    )

                else:
                    # Generic pass-through for other tasks
                    return ExecutionResultArtifact(
                        node_name=node.name,
                        success=True,
                        output={"status": "completed"},
                        duration=time.perf_counter() - node_start,
                    )
            except Exception as exc:
                return ExecutionResultArtifact(
                    node_name=node.name,
                    success=False,
                    error=str(exc),
                    duration=time.perf_counter() - node_start,
                )

        policy = ExecutionPolicy(
            max_retries=2,
            retry_strategy=RetryStrategy.EXPONENTIAL,
            base_delay_seconds=2.0,
        )
        engine = ExecutionEngine(policy=policy)
        return engine.execute(graph, handler=default_handler)

    def _derive_project_name(self, requirements: Dict[str, Any], fallback: str) -> str:
        project = requirements.get("project", "")
        if project and str(project).strip():
            return str(project).strip().lower().replace(" ", "_")
        return fallback.strip().lower().replace(" ", "_")[:40]

    @staticmethod
    def _project_dict(context: ProjectContext) -> Dict[str, Any]:
        """Build a minimal project dict for validator usage."""
        return {
            "project_name": context.project_name,
            "folders": context.architecture.get("folders", []),
            "files": [],
        }

    def _fail(self, context: ProjectContext, stage: str, error: str, started: float) -> ExecutionResult:
        context.status = "failed"
        context.add_error(error)
        Logger.error(f"[EngineeringPipeline] Failed at {stage}: {error}")
        return self._finalize(context, started, success=False, message=f"Pipeline failed at {stage}: {error}")

    def _finalize(self, context: ProjectContext, started: float, success: bool, message: str) -> ExecutionResult:
        duration = time.perf_counter() - started if started else 0.0
        return ExecutionResult(
            success=success,
            status="completed" if success else "failed",
            message=message,
            data=context.to_dict(),
            metrics={"duration": round(duration, 3)},
            warnings=list(context.warnings),
            errors=list(context.errors),
            artifacts=list(context.artifacts),
            duration=duration,
        )
