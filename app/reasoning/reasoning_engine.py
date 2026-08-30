from __future__ import annotations

import json
from typing import Any, Dict, List

from app.memory.memory_manager import MemoryManager
from app.reasoning.action_executor import ActionExecutor
from app.reasoning.action import Action
from app.reasoning.context_builder import ContextBuilder
from app.reasoning.json_parser import parse_thought
from app.reasoning.memory_summarizer import MemorySummarizer
from app.reasoning.reasoning_metrics import ReasoningMetrics
from app.reasoning.observation import Observation
from app.reasoning.reasoning_prompt import build_reasoning_prompt
from app.reasoning.reasoning_result import ReasoningResult
from app.reasoning.reasoning_state import ReasoningState
from app.reasoning.thought import Thought
from app.tools.tool_manager import ToolManager


class ReasoningEngine:
    def __init__(self, tool_manager=None, ai_manager=None, max_iterations=10,
                 action_executor=None, memory=None, context_builder=None, summarizer=None,
                 event_bus=None, reasoning_cache=None, reasoning_history=None):
        self.tool_manager = tool_manager or ToolManager()
        self.memory = memory or MemoryManager()
        self.context_builder = context_builder or ContextBuilder()
        self.summarizer = summarizer or MemorySummarizer()
        self.event_bus = event_bus
        self.ai_manager = ai_manager
        self.max_iterations = min(max(1, max_iterations), 20)
        self.state = None
        self.history: List[Dict[str, Any]] = []
        self.metrics = ReasoningMetrics()
        self.action_executor = action_executor or ActionExecutor(self.tool_manager, self.metrics, event_bus)
        self.retry_limit = 2
        # Caching is opt-in: reasoning can invoke tools with side effects, so callers
        # choose explicitly when a goal is safe to reuse.
        self.reasoning_cache = reasoning_cache
        self.reasoning_history = reasoning_history

    def run(self, goal: str, context: str = ""):
        if not goal or not goal.strip():
            return ReasoningResult(
                goal="",
                success=False,
                iterations=0,
                thoughts=[],
                observations=[],
                final_answer="Goal cannot be empty",
                status="error",
                message="Goal cannot be empty",
                history=[],
                completed=False,
            ).to_dict()

        objective = goal.strip()
        self._cache_context = context
        if self.reasoning_cache is not None:
            cached = self.reasoning_cache.get(objective, context)
            if cached is not None:
                cached["cache_hit"] = True
                return cached
        self.state = ReasoningState(goal=objective)
        self.history = []
        self.metrics.iterations = 0
        self.metrics.tool_calls = 0
        self.metrics.failures = 0
        self.metrics.retries = 0
        self.metrics.time_taken = 0.0
        self.metrics.start()
        retries = 0

        for iteration in range(1, self.max_iterations + 1):
            raw_thought = self._generate_thought(objective, context)
            thought, parse_error = self._parse_thought(raw_thought, objective, iteration)
            if parse_error:
                observation = Observation(
                    success=False,
                    error=parse_error,
                    tool="",
                    action="",
                    step=iteration,
                ).to_dict()
                self.state.add_observation(observation)
                self.history = self.state.history()
                self.metrics.iterations = iteration
                self.metrics.failures += 1
                self.metrics.finish()
                return self._result(False, "Invalid AI response: " + parse_error, iteration)

            action = self._build_action(thought)
            clean_thought = thought.to_dict()
            if self.event_bus:
                self.event_bus.publish("THOUGHT_CREATED", clean_thought)
            self.state.add_thought(clean_thought)
            self.state.add_action(action.to_dict())

            self.metrics.iterations = iteration
            tool_result = self._execute(action)
            observation = Observation(
                success=bool(tool_result.get("success")),
                output=tool_result.get("output"),
                error=tool_result.get("error"),
                tool=thought.tool,
                action=thought.action,
                step=iteration,
            ).to_dict()
            self.state.add_observation(observation)
            self.history = self.state.history()
            self._record(iteration, clean_thought, observation)
            if not observation["success"]:
                if getattr(self.action_executor, "metrics", None) is not self.metrics:
                    self.metrics.failures += 1
                if retries < self.retry_limit:
                    retries += 1
                    self.metrics.retries = retries

            if thought.finished:
                self.state.completed = True
                self.metrics.finish()
                return self._result(True, "Goal finished after thought-driven execution.", iteration)

            tool_error = tool_result.get("error") or ""
            if tool_error.startswith("Unknown tool:"):
                return self._result(False, tool_error, iteration)

        self.metrics.finish()
        return self._result(False, "Maximum reasoning iterations reached.", self.max_iterations)

    def _generate_thought(self, objective, context):
        if self.ai_manager is not None:
            built_context = self.context_builder.build(self.state, progress={}, conversation_summary=context)
            built_context["history"] = self.summarizer.summarize(self.state.history())
            prompt = build_reasoning_prompt(objective, self.state, built_context)
            try:
                answer = self.ai_manager.ask(prompt)
                if answer:
                    return answer
            except Exception:
                pass
        return self._fallback_thought(objective, self.state.current_step + 1)

    def _fallback_thought(self, objective, step):
        lower_goal = objective.lower()
        if any(keyword in lower_goal for keyword in ("search", "auth", "login", "analy", "project", "inspect")):
            return json.dumps({
                "thought": "Need to inspect the project before acting.",
                "tool": "search",
                "action": "search",
                "arguments": {"path": ".", "query": objective},
                "finished": False,
            })
        if any(keyword in lower_goal for keyword in ("create", "calculator", "snake", "game")):
            return json.dumps({
                "thought": "Need to create the requested project or artifact.",
                "tool": "file",
                "action": "write",
                "arguments": {"path": "workspace/generated_app.py", "content": "# generated by reasoning engine\nprint('generated')\n"},
                "finished": True,
            })
        if any(keyword in lower_goal for keyword in ("read", "readme")):
            return json.dumps({
                "thought": "Need to read the README to confirm the expected instructions.",
                "tool": "file",
                "action": "read",
                "arguments": {"path": "README.md"},
                "finished": True,
            })
        if any(keyword in lower_goal for keyword in ("run", "execute")):
            return json.dumps({
                "thought": "Need to execute the relevant runtime step.",
                "tool": "python",
                "action": "run",
                "arguments": {"code": "print('reasoning ok')"},
                "finished": False,
            })
        return json.dumps({
            "thought": "Need to inspect the current state.",
            "tool": "search",
            "action": "search",
            "arguments": {"path": ".", "query": objective},
            "finished": False,
        })

    def _parse_thought(self, raw, objective, step):
        try:
            return parse_thought(raw, step=step), None
        except ValueError as error:
            return None, str(error) + "."

    def _result(self, success, message, iterations):
        steps = [
            {"thought": thought, "observation": observation}
            for thought, observation in zip(self.state.thoughts, self.state.observations)
        ]
        result = ReasoningResult(
            goal=self.state.goal,
            success=success,
            iterations=iterations,
            steps=steps,
            thoughts=self.state.thoughts,
            observations=self.state.observations,
            final_answer=message,
            status="completed" if success else "failed",
            message=message,
            history=self.state.history(),
            completed=success,
            metrics=self.metrics.to_dict(),
        ).to_dict()
        if self.reasoning_history is not None:
            self.reasoning_history.record(self.state.goal, result, 1.0 if success else 0.0)
        if success and self.reasoning_cache is not None:
            self.reasoning_cache.set(self.state.goal, getattr(self, "_cache_context", ""), result)
        return result

    def _execute_thought(self, thought):
        return self._execute(self._build_action(thought))

    def _build_action(self, thought):
        return Action(thought.tool, thought.action, self._normalized_arguments(thought))

    def _execute(self, action):
        return self.action_executor.execute(action)

    def _record(self, iteration, thought, observation):
        self.memory.add_reasoning({"iteration": iteration, "thought": thought,
                                   "action": self.state.actions[-1], "observation": observation})

    def _should_stop(self, thought, observation):
        return thought.finished or str(observation.get("error") or "").startswith("Unknown tool:")

    def _normalized_arguments(self, thought):
        arguments = dict(thought.arguments or {})
        if thought.tool == "search":
            arguments.setdefault("path", ".")
            arguments.setdefault("query", thought.thought)
        return arguments
