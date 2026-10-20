from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Any, Callable, Dict, Optional

from app.eos.context import ExecutionContext
from app.eos.goal import Goal
from app.eos.metrics import EOSMetrics
from app.eos.mission import Mission
from app.eos.quality import QualityGate
from app.eos.state_machine import EOSState, EOSStateMachine
from app.eos.workflow import Workflow, WorkflowStage
from app.reasoning.goal_analyzer import GoalAnalyzer
from app.events.event_bus import EventBus
from app.reports.execution_report import ExecutionReport
from app.eos.result import AgentResult
from app.eos.retry import RetryPolicy
from app.eos.timeout import TimeoutPolicy
from app.eos.status import TaskStatus
from app.core.logger import Logger


class AgentExecutor:
    """Execute one agent task with retries, timeout, and structured logging."""

    def __init__(
        self,
        retry_policy: Optional[RetryPolicy] = None,
        timeout_policy: Optional[TimeoutPolicy] = None,
        metrics: Any = None,
    ) -> None:
        self.retry_policy = retry_policy or RetryPolicy()
        self.timeout_policy = timeout_policy or TimeoutPolicy()
        self.metrics = metrics

    def execute(self, agent: Any, task: Any) -> AgentResult:
        name = self._agent_name(agent)
        started = time.perf_counter()
        attempts = 0
        result = AgentResult(False, error="Execution did not start", agent=name)
        if hasattr(task, "status"):
            task.status = TaskStatus.RUNNING
        while attempts <= self.retry_policy.max_retry:
            attempts += 1
            try:
                result = self._invoke(agent, task, name)
            except TimeoutError:
                result = AgentResult(False, error="Agent execution timed out", agent=name)
                if hasattr(task, "status"):
                    task.status = TaskStatus.TIMED_OUT
            except Exception as error:
                result = AgentResult(False, error=str(error), agent=name)
            if result.success:
                break
            if attempts <= self.retry_policy.max_retry:
                time.sleep(self.retry_policy.delay * self.retry_policy.backoff ** (attempts - 1))
        duration = time.perf_counter() - started
        result.execution_time = duration
        if hasattr(task, "status") and result.success:
            task.status = TaskStatus.COMPLETED
        elif hasattr(task, "status") and task.status != TaskStatus.TIMED_OUT:
            task.status = TaskStatus.FAILED
        record = {
            "task_id": getattr(task, "id", ""),
            "agent": name,
            "capability": getattr(task, "capability", ""),
            "start_time": started,
            "end_time": started + duration,
            "duration": duration,
            "success": result.success,
            "error": result.error,
            "attempts": attempts,
        }
        if self.metrics is not None and hasattr(self.metrics, "record_execution"):
            self.metrics.record_execution(**record)
        Logger.info(f"[EOS] task={record['task_id']} agent={name} success={result.success}")
        return result

    def _invoke(self, agent: Any, task: Any, name: str) -> AgentResult:
        execute = getattr(agent, "execute", None) or getattr(agent, "run", None)
        if not callable(execute):
            raise TypeError(f"Agent {name} does not implement execute or run")
        pool = ThreadPoolExecutor(max_workers=1)
        future = pool.submit(execute, task)
        try:
            value = future.result(timeout=self.timeout_policy.seconds)
        finally:
            pool.shutdown(wait=self.timeout_policy.seconds is None, cancel_futures=True)
        return AgentResult.from_value(value, name)

    @staticmethod
    def _agent_name(agent: Any) -> str:
        name = getattr(agent, "name", getattr(agent, "agent_id", agent.__class__.__name__))
        return str(name() if callable(name) else name)


class EngineeringOS:
    """Data-driven mission controller for the engineering lifecycle."""

    DEFAULT_STAGES = (
        ("understanding", EOSState.UNDERSTANDING),
        ("planning", EOSState.PLANNING),
        ("research", EOSState.RESEARCH),
        ("coding", EOSState.CODING),
        ("testing", EOSState.TESTING),
        ("repair", EOSState.REPAIR),
        ("validation", EOSState.VALIDATION),
        ("documentation", EOSState.DOCUMENTATION),
        ("deployment", EOSState.DEPLOYMENT),
    )

    def __init__(
        self,
        handlers: Optional[Dict[str, Callable[[ExecutionContext], Any]]] = None,
        event_bus: Optional[EventBus] = None,
        goal_analyzer: Optional[GoalAnalyzer] = None,
        quality_gate: Optional[QualityGate] = None,
        workflow: Optional[Workflow] = None,
        report_dir: str = ".jarvis/eos-reports",
    ):
        self.handlers = dict(handlers or {})
        self.event_bus = event_bus or EventBus()
        self.goal_analyzer = goal_analyzer or GoalAnalyzer()
        self.quality_gate = quality_gate or QualityGate()
        self.report_dir = report_dir
        self.workflow = workflow or Workflow(
            [WorkflowStage(name, state.value, self.handlers.get(name, lambda _: None))
             for name, state in self.DEFAULT_STAGES]
        )

    def run(self, text: str) -> Dict[str, Any]:
        goal = Goal(text)
        goal.analysis = self.goal_analyzer.analyze(goal.text)
        mission = Mission(goal=goal)
        context = ExecutionContext(mission=mission, status=EOSState.IDLE.value)
        state_machine = EOSStateMachine()
        metrics = EOSMetrics()
        report = ExecutionReport(goal.text)

        try:
            for stage in self.workflow.stages:
                state = EOSState(stage.state)
                name = stage.name
                state_machine.transition(state, f"{name}_started")
                self.event_bus.publish(f"{name.upper()}_STARTED", {"mission_id": mission.mission_id})
                handler = self.handlers.get(name)
                result = handler(context) if handler else {"status": "ready", "stage": name}
                context.record(name, result)
                mission.results[name] = result
                report.record(name, True)
                metrics.stages_completed += 1
                self.event_bus.publish(f"{name.upper()}_COMPLETED", result)

            quality = self.quality_gate.evaluate(context)
            mission.results["quality"] = quality
            metrics.score = quality["score"]
            report.score = quality["score"]
            state_machine.transition(EOSState.COMPLETED, "mission_completed")
            mission.status = EOSState.COMPLETED.value
        except Exception as error:
            context.errors.append(str(error))
            mission.errors.append(str(error))
            report.record(name if "name" in locals() else "mission", False)
            report.errors.append(str(error))
            metrics.stages_failed += 1
            state_machine.transition(EOSState.FAILED, "mission_failed")
            mission.status = EOSState.FAILED.value

        metrics.finish()
        context.status = mission.status
        report_path = report.save(self.report_dir)
        return {
            "mission_id": mission.mission_id,
            "status": mission.status,
            "goal": goal.analysis,
            "results": mission.results,
            "errors": mission.errors,
            "state_history": state_machine.history,
            "metrics": {
                "duration_seconds": metrics.duration_seconds,
                "stages_completed": metrics.stages_completed,
                "stages_failed": metrics.stages_failed,
                "score": metrics.score,
            },
            "report": report.to_dict(),
            "report_path": str(report_path),
            "context": context,
        }
