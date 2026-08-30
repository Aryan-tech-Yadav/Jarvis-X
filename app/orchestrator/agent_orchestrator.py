"""Phase 1 collaboration pipeline for Jarvis-X project work.

The orchestrator owns sequencing.  Agents receive the shared context through a
message bus and never select or call the next specialist themselves.
"""

from datetime import datetime, timezone

from app.agents.agent_registry import AgentRegistry
from app.agents.coder_agent import CoderAgent
from app.agents.documentation_agent import DocumentationAgent
from app.agents.message_bus import MessageBus
from app.agents.planner_agent import PlannerAgent
from app.agents.reviewer_agent import ReviewerAgent
from app.agents.task import AgentTask
from app.agents.task_queue import AgentTaskQueue
from app.agents.tester_agent import TesterAgent
from app.events.event_bus import EventBus
from app.events.event_types import (
    AGENT_STARTED,
    PLAN_CREATED,
    PROJECT_FINISHED,
    REPAIR_DONE,
    STEP_COMPLETED,
    VALIDATION_FAILED,
)
from app.orchestrator.shared_context import SharedContext
from app.core.results import ExecutionResult


PIPELINE = ("planner", "coder", "tester", "reviewer", "documentation")


class AgentOrchestrator:
    """Coordinate the planner → coder → tester → reviewer → docs lifecycle."""

    def __init__(self, registry=None, project_manager=None, message_bus=None, task_queue=None, event_bus=None, max_retries=1):
        self.registry = registry or self._default_registry(project_manager)
        self.message_bus = message_bus or MessageBus()
        self.task_queue = task_queue or AgentTaskQueue()
        self.event_bus = event_bus or EventBus()
        self.max_retries = max(0, max_retries)

    def run(self, goal=None, project_path=None, context=None):
        context = self._context(goal, project_path, context)
        retries = {name: 0 for name in PIPELINE}
        self.task_queue.enqueue(AgentTask(title=context.goal if hasattr(context, "goal") else context["goal"], agent="planner"))

        while task := self.task_queue.dequeue():
            agent_name = task.agent
            self._set(context, "current_step", agent_name)
            entry = {"agent": agent_name, "started_at": self._now(), "status": "running"}
            self._timeline(context).append(entry)
            self._publish(AGENT_STARTED, context, {"agent": agent_name})

            agent = self.registry.get(agent_name)
            if agent is None:
                return self._finish_failure(context, task, entry, f"Agent not registered: {agent_name}")

            self.message_bus.send("orchestrator", agent_name, "task", context)
            message = self.message_bus.receive(agent_name)
            result = self._execute(agent, message.payload)
            entry["finished_at"] = self._now()
            entry["status"] = "completed" if result["success"] else "failed"
            self._add_progress(context, agent_name, result)

            if result["success"]:
                self.task_queue.complete(task, result)
                self._publish(STEP_COMPLETED, context, {"agent": agent_name, "result": result.get("output")})
                if agent_name == "planner":
                    self._publish(PLAN_CREATED, context, {"plan": result.get("output")})
                if agent_name == "coder" and self._get(context, "operation") == "repair":
                    self._publish(REPAIR_DONE, context, {"result": result.get("output")})
                next_agent = self._next_agent(agent_name)
                if next_agent:
                    self.task_queue.enqueue(AgentTask(title=task.title, agent=next_agent))
                    continue
                return self._finish_success(context)

            self.task_queue.fail(task, result)
            response = self._retry_or_fail(context, task, entry, result, retries)
            if response is not None:
                return response

        return self._finish_failure(context, None, None, "Task queue ended before the project was completed")

    execute = run

    def run_result(self, goal=None, project_path=None, context=None):
        """Run the existing collaboration flow behind the shared result model."""
        result = ExecutionResult.timed(self.run, goal, project_path, context)
        if result.success:
            context_value = result.data.get("context") if isinstance(result.data, dict) else None
            timeline = result.data.get("timeline", []) if isinstance(result.data, dict) else []
            result.message = "Multi-agent pipeline complete"
            result.metrics.update({"agent_steps": len(timeline), "events": len(getattr(context_value, "events", []))})
            if context_value and getattr(context_value, "project_path", None):
                result.artifacts.append(context_value.project_path)
            warning = getattr(context_value, "documentation_warning", None)
            if warning:
                result.warnings.append(str(warning))
        return result

    def _retry_or_fail(self, context, task, entry, result, retries):
        agent_name = task.agent
        if agent_name == "documentation":
            # Documentation must not roll back a validated project.
            self._set(context, "documentation_warning", result.get("output"))
            return self._finish_success(context)

        if agent_name == "planner" and retries[agent_name] < self.max_retries:
            retries[agent_name] += 1
            self.task_queue.enqueue(AgentTask(title=task.title, agent="planner"))
            return None

        if agent_name in {"tester", "reviewer"} and retries[agent_name] < self.max_retries:
            retries[agent_name] += 1
            issue = result.get("output")
            self._set(context, "operation", "repair")
            self._set(context, "repair_request", issue)
            self._publish(VALIDATION_FAILED, context, {"agent": agent_name, "result": issue})
            self.task_queue.enqueue(AgentTask(title=task.title, agent="coder"))
            return None

        if agent_name == "coder" and retries[agent_name] < self.max_retries:
            retries[agent_name] += 1
            self.task_queue.enqueue(AgentTask(title=task.title, agent="coder"))
            return None

        return self._finish_failure(context, task, entry, result.get("output", "Agent failed"))

    def _execute(self, agent, context):
        try:
            handler = getattr(agent, "execute", None) or getattr(agent, "run", None)
            result = handler(context)
        except Exception as error:  # agents are isolated by design
            result = {"success": False, "output": str(error), "error": str(error)}
        if not isinstance(result, dict):
            return {"success": False, "output": "Agent returned an invalid result"}
        result.setdefault("success", False)
        result.setdefault("output", None)
        return result

    def _finish_success(self, context):
        self._set(context, "current_step", "complete")
        self._publish(PROJECT_FINISHED, context, {"success": True})
        return {"success": True, "output": "Multi-agent pipeline complete", "context": context, "timeline": self._timeline(context)}

    def _finish_failure(self, context, task, entry, output):
        if entry is not None and not entry.get("finished_at"):
            entry["finished_at"] = self._now()
            entry["status"] = "failed"
        failed_agent = task.agent if task is not None else self._get(context, "current_step")
        self._set(context, "current_step", "failed")
        self._publish(PROJECT_FINISHED, context, {"success": False, "failed_agent": failed_agent, "output": output})
        return {
            "success": False,
            "failed_agent": failed_agent,
            "output": output,
            "context": context,
            "timeline": self._timeline(context),
        }

    @staticmethod
    def _default_registry(project_manager=None):
        registry = AgentRegistry()
        registry.register(PlannerAgent())
        registry.register(CoderAgent(project_manager))
        registry.register(TesterAgent(project_manager))
        registry.register(ReviewerAgent())
        registry.register(DocumentationAgent())
        return registry

    @staticmethod
    def _next_agent(agent_name):
        index = PIPELINE.index(agent_name)
        return PIPELINE[index + 1] if index + 1 < len(PIPELINE) else None

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    def _publish(self, event_type, context, payload):
        event = self.event_bus.publish(event_type, payload)
        self._events(context).append(event.to_dict())
        return event

    @staticmethod
    def _context(goal, project_path, context):
        if context is None:
            if not isinstance(goal, str) or not goal.strip():
                raise ValueError("Goal cannot be empty")
            return SharedContext(goal=goal.strip(), base_path=project_path)
        if isinstance(context, SharedContext):
            if project_path:
                context.project_path = project_path
            return context
        if isinstance(context, dict):
            context.setdefault("goal", goal)
            if not isinstance(context["goal"], str) or not context["goal"].strip():
                raise ValueError("Goal cannot be empty")
            context.setdefault("project_path", project_path)
            context.setdefault("memory", {})
            context.setdefault("timeline", [])
            context.setdefault("events", [])
            context.setdefault("progress", [])
            context.setdefault("outputs", {})
            return context
        raise TypeError("context must be a SharedContext or dictionary")

    @staticmethod
    def _get(context, key, default=None):
        return context.get(key, default) if isinstance(context, dict) else getattr(context, key, default)

    @staticmethod
    def _set(context, key, value):
        if isinstance(context, dict):
            context[key] = value
        else:
            setattr(context, key, value)

    def _timeline(self, context):
        timeline = self._get(context, "timeline")
        if timeline is None:
            timeline = []
            self._set(context, "timeline", timeline)
        return timeline

    def _events(self, context):
        events = self._get(context, "events")
        if events is None:
            events = []
            self._set(context, "events", events)
        return events

    def _add_progress(self, context, agent_name, result):
        if hasattr(context, "add_progress"):
            context.add_progress(agent_name, result)
            return
        context["progress"].append({"agent": agent_name, "result": result})
        context["outputs"][agent_name] = result.get("output")
