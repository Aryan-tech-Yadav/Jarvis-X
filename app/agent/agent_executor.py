from __future__ import annotations

from typing import Any, Dict

from app.agent.agent_state import AgentState
from app.reasoning.reasoning_engine import ReasoningEngine
from app.tools.tool_manager import ToolManager


class AgentExecutor:
    """Owns one autonomous task lifecycle around the reasoning engine."""

    def __init__(self, reasoning_engine=None, tool_manager=None, ai_manager=None, max_iterations=20):
        self.tool_manager = tool_manager or ToolManager()
        self.reasoning_engine = reasoning_engine or ReasoningEngine(
            tool_manager=self.tool_manager,
            ai_manager=ai_manager,
            max_iterations=max_iterations,
        )
        self.state = None
        self._cancelled = False

    def run(self, goal: str, context: str = "") -> Dict[str, Any]:
        if not goal or not goal.strip():
            return {
                "success": False,
                "goal": "",
                "iterations": 0,
                "actions": [],
                "observations": [],
                "result": "Goal cannot be empty",
                "status": "failed",
            }

        self._cancelled = False
        self.state = AgentState(goal=goal.strip(), status="running")
        reasoning_result = self.reasoning_engine.run(self.state.goal, context=context)
        self.state.record(reasoning_result)
        self.state.status = "completed" if reasoning_result.get("success") else "failed"

        if self._cancelled:
            return self._cancelled_result()

        return {
            "success": reasoning_result.get("success", False),
            "goal": self.state.goal,
            "iterations": self.state.iteration,
            "actions": self.state.tool_history,
            "observations": self.state.observation_history,
            "result": reasoning_result.get("final_answer", ""),
            "status": self.state.status,
        }

    def cancel(self):
        self._cancelled = True
        if self.state is not None:
            self.state.status = "cancelled"

    def _cancelled_result(self):
        return {
            "success": False,
            "goal": self.state.goal if self.state else "",
            "iterations": self.state.iteration if self.state else 0,
            "actions": self.state.tool_history if self.state else [],
            "observations": self.state.observation_history if self.state else [],
            "result": "Task cancelled by user",
            "status": "cancelled",
        }