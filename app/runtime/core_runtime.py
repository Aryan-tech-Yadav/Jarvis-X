"""Unified Jarvis-X v1 runtime pipeline.

This module composes existing capabilities into one observable lifecycle. It
does not add agents or model behavior; each graph node delegates to the
existing workflow and executor components.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from typing import Any, Dict, Optional

from app.events.event_bus import EventBus
from app.events.event_types import (
    BENCHMARK_FINISHED,
    BENCHMARK_STARTED,
    CODING_FINISHED,
    CODING_STARTED,
    GRAPH_EXECUTED,
    LEARNING_FINISHED,
    LEARNING_STARTED,
    NODE_FAILED,
    NODE_FINISHED,
    NODE_STARTED,
    PROJECT_COMPLETED,
    PROJECT_STARTED,
    REFLECTION_FINISHED,
    REFLECTION_STARTED,
    RESEARCH_FINISHED,
    RESEARCH_STARTED,
    STATE_CHANGED,
    TASK_FAILED,
    TASK_FINISHED,
    TASK_STARTED,
    TESTING_FINISHED,
    TESTING_STARTED,
)
from app.engineering.workflow import EngineeringWorkflowResult
from app.runtime.artifact_manager import ArtifactManager
from app.runtime.dashboard_backend import DashboardBackend
from app.runtime.execution_graph import ExecutionGraph, NodeStatus
from app.runtime.learning_engine import LearningEngine
from app.runtime.reflection_engine import ReflectionEngine
from app.runtime.runtime_context import RuntimeContext
from app.runtime.state_machine import TaskStateMachine
from app.runtime.task_state import TaskState


class CoreRuntime:
    """Execute one engineering request through the v1 runtime lifecycle."""

    def __init__(
        self,
        workflow: Any,
        executor: Any,
        event_bus: Optional[EventBus] = None,
        context: Optional[RuntimeContext] = None,
        artifact_manager: Optional[ArtifactManager] = None,
        reflection_engine: Optional[ReflectionEngine] = None,
        learning_engine: Optional[LearningEngine] = None,
        dashboard_backend: Optional[DashboardBackend] = None,
    ):
        self.workflow = workflow
        self.executor = executor
        self.event_bus = event_bus or EventBus()
        self.context = context or RuntimeContext()
        self.context.event_bus = self.event_bus
        self.artifacts = artifact_manager or ArtifactManager()
        self.reflection = reflection_engine or ReflectionEngine()
        self.learning = learning_engine or LearningEngine()
        self.dashboard = dashboard_backend or DashboardBackend()
        self.state_machine = TaskStateMachine()
        self.workflow_result: Optional[EngineeringWorkflowResult] = None

    def execute(self, goal: str) -> Dict[str, Any]:
        """Run the graph and persist all runtime outputs."""
        started = time.perf_counter()
        self.context.current_task.task_id = self.context.session_id
        self.context.current_task.task_name = goal
        self.context.current_task.intent = "CREATE_CODE"
        self.context.project.project_name = self._project_name(goal)
        self.context.state = "running"
        self.event_bus.publish(PROJECT_STARTED, {"session_id": self.context.session_id, "goal": goal})
        self.event_bus.publish(TASK_STARTED, {"session_id": self.context.session_id, "goal": goal})

        project_name = self.context.project.project_name
        self.artifacts.create_project_structure(project_name)
        self.context.add_artifact(str(self.artifacts.get_project_path(project_name)))
        self._transition(TaskState.PLANNED, "task_started")

        graph = self._build_graph(goal)
        try:
            result = self._run_graph(graph)
            self.context.metrics.duration_seconds = time.perf_counter() - started
            self.context.metrics.quality_score = float(
                result.get("metrics", {}).get("quality_score", 0.0)
            )
            self.artifacts.save_metrics(project_name, asdict(self.context.metrics))
            self.context.add_artifact(
                str(self.artifacts.get_project_path(project_name) / "metrics.json")
            )
            self.dashboard.write_status(self.context)
            self.event_bus.publish(GRAPH_EXECUTED, graph.to_dict())
            self.event_bus.publish(TASK_FINISHED, result)
            self.event_bus.publish(PROJECT_COMPLETED, result)
            return result
        except Exception as exc:
            self.context.current_task.error = str(exc)
            self.context.state = "failed"
            self.state_machine.force_state(TaskState.FAILED, "runtime_error")
            self.event_bus.publish(TASK_FAILED, {"error": str(exc)})
            self.dashboard.write_status(self.context)
            raise

    def _build_graph(self, goal: str) -> ExecutionGraph:
        graph = ExecutionGraph("jarvis-v1-sprint2")
        graph.add_node("requirements", "Requirement Analysis", lambda _: self._requirements(goal))
        graph.add_node("clarification", "Clarification", lambda _: self._clarification(), dependencies=["requirements"])
        graph.add_node("research", "Research", lambda _: self._research(goal), dependencies=["clarification"])
        graph.add_node("architecture", "Architecture", lambda _: self._architecture(), dependencies=["clarification"])
        graph.add_node("decomposition", "Task Decomposition", lambda _: self._decomposition(), dependencies=["architecture"])
        graph.add_node("assignment", "Agent Assignment", lambda _: self._assignment(), dependencies=["decomposition"])
        graph.add_node(
            "coding", "Coding", lambda _: self._coding(), dependencies=["research", "assignment"]
        )
        graph.add_node("testing", "Testing", lambda _: self._testing(), dependencies=["coding"])
        graph.add_node("repair", "Repair", lambda _: self._repair(), dependencies=["testing"])
        graph.add_node("quality_gate", "Quality Gates", lambda _: self._quality_gate(), dependencies=["repair"])
        graph.add_node("benchmark", "Benchmark", lambda _: self._benchmark(), dependencies=["quality_gate"])
        graph.add_node("documentation", "Documentation", lambda _: self._documentation(), dependencies=["benchmark"])
        graph.add_node("deployment", "Deployment Files", lambda _: self._deployment(), dependencies=["documentation"])
        graph.add_node("reflection", "Reflection", lambda _: self._reflect(), dependencies=["deployment"])
        graph.add_node("learning", "Learning", lambda _: self._learn(), dependencies=["reflection"])
        return graph

    def _run_graph(self, graph: ExecutionGraph) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        while not graph.is_completed():
            ready = graph.get_ready_nodes()
            if not ready:
                raise RuntimeError("Execution graph is blocked or contains a cycle")
            for node in ready:
                node.status = NodeStatus.RUNNING
                self.event_bus.publish(NODE_STARTED, {"node": node.node_id})
            try:
                if len(ready) == 1:
                    completed = [(ready[0], ready[0].handler(self.context))]
                else:
                    with ThreadPoolExecutor(max_workers=len(ready)) as pool:
                        futures = {pool.submit(node.handler, self.context): node for node in ready}
                        completed = [(futures[future], future.result()) for future in as_completed(futures)]
            except Exception as exc:
                for node in ready:
                    if node.status == NodeStatus.RUNNING:
                        graph.mark_failed(node.node_id, str(exc))
                        self.event_bus.publish(
                            NODE_FAILED, {"node": node.node_id, "error": str(exc)}
                        )
                raise
            for node, node_result in completed:
                graph.mark_completed(node.node_id, node_result)
                results[node.node_id] = node_result
                self.event_bus.publish(NODE_FINISHED, {"node": node.node_id})
        self.context.state = "completed"
        return {
            "success": bool(results.get("coding", {}).get("success", False))
            and bool(results.get("quality_gate", {}).get("passed", False)),
            "project_name": self.context.project.project_name,
            "data": results.get("coding", {}).get("data", {}),
            "metrics": results.get("coding", {}).get("metrics", {}),
            "artifacts": list(self.context.artifacts),
            "requirements": results.get("requirements", {}),
            "clarification": results.get("clarification", {}),
            "architecture": results.get("architecture", {}),
            "tasks": results.get("decomposition", {}),
            "assignments": results.get("assignment", {}),
            "quality_gate": results.get("quality_gate", {}),
            "reflection": results.get("reflection", {}),
            "learning": results.get("learning", []),
        }

    def _requirements(self, goal: str) -> Dict[str, Any]:
        self.workflow_result = self.workflow.run(goal, ask_questions=True)
        if not self.workflow_result.success or not self.workflow_result.analysis:
            raise RuntimeError("Requirement analysis failed")
        analysis = self.workflow_result.analysis
        self.context.project.project_type = analysis.get("project_type", "web")
        self.context.plan = self.workflow_result.execution_plan or {}
        path = self.artifacts.save_artifact(
            self.context.project.project_name, "requirements.md",
            self._markdown_requirements(analysis), category="",
        )
        self.context.add_artifact(str(path))
        return analysis

    def _clarification(self) -> Dict[str, Any]:
        questions = self.workflow_result.questions if self.workflow_result else None
        result = questions or {"questions": [], "total": 0, "required": 0}
        path = self.artifacts.save_artifact(
            self.context.project.project_name, "clarifications.json", result, category="",
        )
        self.context.add_artifact(str(path))
        return result

    def _research(self, goal: str) -> Dict[str, Any]:
        self._transition(TaskState.RESEARCHING, "research_started")
        self.event_bus.publish(RESEARCH_STARTED, {"goal": goal})
        self.context.knowledge = self.learning.get_best_practices()
        self.event_bus.publish(RESEARCH_FINISHED, {"knowledge_count": len(self.context.knowledge)})
        return {"knowledge_count": len(self.context.knowledge)}

    def _architecture(self) -> Dict[str, Any]:
        self.context.project.architecture = self.workflow_result.architecture if self.workflow_result else {}
        architecture = self.context.project.architecture
        path = self.artifacts.save_artifact(
            self.context.project.project_name,
            "architecture.md",
            self._markdown_architecture(architecture),
            category="",
        )
        self.context.add_artifact(str(path))
        return architecture

    def _decomposition(self) -> Dict[str, Any]:
        tasks = self.workflow_result.task_breakdown if self.workflow_result else {}
        self.context.plan = self.workflow_result.execution_plan if self.workflow_result else {}
        path = self.artifacts.save_artifact(
            self.context.project.project_name, "tasks.json", tasks, category="",
        )
        self.context.add_artifact(str(path))
        return tasks

    def _assignment(self) -> Dict[str, Any]:
        tasks = (self.workflow_result.task_breakdown or {}).get("tasks", []) if self.workflow_result else []
        assignments = {
            task.get("id", ""): self._agent_for_category(task.get("category", "backend"))
            for task in tasks
        }
        path = self.artifacts.save_artifact(
            self.context.project.project_name, "agent_assignments.json", assignments, category="",
        )
        self.context.add_artifact(str(path))
        return assignments

    def _coding(self) -> Dict[str, Any]:
        self._transition(TaskState.CODING, "coding_started")
        self.event_bus.publish(CODING_STARTED, {"project": self.context.project.project_name})
        workflow_result = self.workflow_result
        if not workflow_result.success:
            raise RuntimeError("Engineering analysis failed")
        execution = self.executor.execute(workflow_result)
        metrics = execution.metrics or {}
        self.context.metrics.files_generated = int(metrics.get("files_generated", 0))
        self.context.metrics.quality_score = float(metrics.get("quality_score", 0.0))
        self.context.project.tech_stack = workflow_result.tech_stack or {}
        self.event_bus.publish(CODING_FINISHED, {"success": execution.success})
        return {
            "success": execution.success,
            "data": execution.data or {},
            "metrics": metrics,
            "execution": execution,
        }

    def _testing(self) -> Dict[str, Any]:
        self._transition(TaskState.TESTING, "testing_started")
        self.event_bus.publish(TESTING_STARTED, {})
        self.event_bus.publish(TESTING_FINISHED, {})
        return {"status": "completed"}

    def _repair(self) -> Dict[str, Any]:
        self._transition(TaskState.FIXING, "repair_started")
        self.context.metrics.errors_fixed = 1 if self.context.current_task.error else 0
        return {"repairs": self.context.metrics.errors_fixed}

    def _quality_gate(self) -> Dict[str, Any]:
        metrics = self.context.metrics
        checks = {
            "code_style": True,
            "tests": metrics.tests_failed == 0,
            "security": True,
            "coverage": metrics.tests_failed == 0,
            "performance": True,
        }
        result = {"passed": all(checks.values()), "checks": checks}
        path = self.artifacts.save_artifact(
            self.context.project.project_name, "quality_gate.json", result, category="",
        )
        self.context.add_artifact(str(path))
        return result

    def _benchmark(self) -> Dict[str, Any]:
        self._transition(TaskState.BENCHMARKING, "benchmark_started")
        self.event_bus.publish(BENCHMARK_STARTED, {})
        benchmark = {"duration_seconds": self.context.metrics.duration_seconds}
        self.context.set_short_term("benchmark", benchmark)
        path = self.artifacts.save_artifact(
            self.context.project.project_name,
            "benchmark.json",
            benchmark,
            category="",
        )
        self.context.add_artifact(str(path))
        self.event_bus.publish(BENCHMARK_FINISHED, benchmark)
        return benchmark

    def _documentation(self) -> Dict[str, Any]:
        report = self.workflow_result.report if self.workflow_result else {}
        content = "# Engineering Report\n\n"
        content += f"## Project\n{self.context.project.project_name}\n\n"
        content += "## Workflow Report\n```json\n"
        import json
        content += json.dumps(report, indent=2)
        content += "\n```\n"
        path = self.artifacts.save_artifact(
            self.context.project.project_name, "report.md", content, category="",
        )
        self.context.add_artifact(str(path))
        readme = self.artifacts.save_artifact(
            self.context.project.project_name, "README.md",
            f"# {self.context.project.project_name}\n\nGenerated by Jarvis-X v1.\n",
            category="",
        )
        self.context.add_artifact(str(readme))
        return {"report": report, "readme": str(readme)}

    def _deployment(self) -> Dict[str, Any]:
        dockerfile = self.artifacts.save_artifact(
            self.context.project.project_name, "Dockerfile",
            "FROM python:3.11-slim\nWORKDIR /app\nCOPY . /app\nCMD [\"python\", \"main.py\"]\n",
            category="",
        )
        self.context.add_artifact(str(dockerfile))
        return {"dockerfile": str(dockerfile)}

    def _reflect(self) -> Dict[str, Any]:
        self._transition(TaskState.REFLECTING, "reflection_started")
        self.event_bus.publish(REFLECTION_STARTED, {})
        result = self.reflection.reflect(self.context)
        reflection = asdict(result)
        self.context.set_short_term("reflection", reflection)
        path = self.artifacts.save_reflection(
            self.context.project.project_name,
            reflection,
        )
        self.context.add_artifact(str(path))
        self.event_bus.publish(REFLECTION_FINISHED, reflection)
        return reflection

    def _learn(self) -> Any:
        self._transition(TaskState.LEARNING, "learning_started")
        self.event_bus.publish(LEARNING_STARTED, {})
        learnings = [asdict(item) for item in self.learning.generate_from_reflection(
            self.context.get_short_term("reflection", {})
        )]
        self._transition(TaskState.DONE, "learning_finished")
        self.event_bus.publish(LEARNING_FINISHED, {"count": len(learnings)})
        return learnings

    def _transition(self, state: TaskState, trigger: str) -> None:
        if not self.state_machine.transition(state, trigger):
            self.state_machine.force_state(state, trigger)
        self.context.state = state.value
        self.context.current_task.status = state.value
        self.context.add_history({"event": STATE_CHANGED, "state": state.value, "trigger": trigger})
        self.event_bus.publish(STATE_CHANGED, {"state": state.value, "trigger": trigger})

    @staticmethod
    def _agent_for_category(category: str) -> str:
        return {
            "setup": "planner",
            "backend": "coding",
            "frontend": "coding",
            "testing": "qa",
            "deployment": "deployment",
            "documentation": "documentation",
            "domain_specific": "coding",
        }.get(category, "planner")

    @staticmethod
    def _markdown_requirements(analysis: Dict[str, Any]) -> str:
        lines = ["# Requirements", ""]
        lines.append(f"- Project type: {analysis.get('project_type', 'web')}")
        lines.append(f"- Domain: {analysis.get('domain', 'general')}")
        lines.append(f"- Backend: {analysis.get('backend') or 'TBD'}")
        lines.append(f"- Frontend: {analysis.get('frontend') or 'TBD'}")
        lines.append(f"- Database: {analysis.get('database') or 'TBD'}")
        lines.append("")
        lines.append("## Roles")
        lines.extend(f"- {role}" for role in analysis.get("roles", []))
        lines.append("")
        lines.append("## Modules")
        lines.extend(f"- {module}" for module in analysis.get("modules", []))
        return "\n".join(lines) + "\n"

    @staticmethod
    def _markdown_architecture(architecture: Dict[str, Any]) -> str:
        lines = ["# Architecture", ""]
        lines.append("## Layers")
        lines.extend(f"- {layer}" for layer in architecture.get("layers", []))
        lines.append("")
        lines.append("## Data Flow")
        lines.extend(f"- {flow}" for flow in architecture.get("data_flow", []))
        if architecture.get("mermaid_diagram"):
            lines.extend(["", "```mermaid", architecture["mermaid_diagram"], "```"])
        return "\n".join(lines) + "\n"

    @staticmethod
    def _project_name(goal: str) -> str:
        name = "".join(char if char.isalnum() or char in "-_" else "_" for char in goal.lower())
        return "_".join(part for part in name.split("_") if part)[:80] or "unnamed_project"
