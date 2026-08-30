"""Autonomous Tool Router for sequencing multi-tool execution pipelines."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.results import ExecutionResult
from .tool_executor import ToolExecutor
from .tool_selector import ToolSelector


class ToolRouter:
    """Routes high-level task workflows through optimal sequences of tools."""

    def __init__(self, selector: Optional[ToolSelector] = None, executor: Optional[ToolExecutor] = None):
        self.selector = selector or ToolSelector()
        self.executor = executor or ToolExecutor()

    def route_and_execute(self, task_intent: str, *args, **kwargs) -> ExecutionResult:
        capability = self.selector.select_tool_for_task(task_intent)
        if not capability:
            return ExecutionResult.failed(f"No suitable tool found for intent: '{task_intent}'")

        return self.executor.execute_tool(capability.name, *args, **kwargs)

    def execute_pipeline(self, pipeline_steps: List[Dict[str, Any]]) -> ExecutionResult:
        results = []
        for step in pipeline_steps:
            tool_name = step.get("tool")
            args = step.get("args", [])
            kwargs = step.get("kwargs", {})
            res = self.executor.execute_tool(tool_name, *args, **kwargs)
            results.append({"step": step.get("name", tool_name), "result": res.to_dict()})
            if not res.success:
                return ExecutionResult.failed(
                    f"Pipeline aborted at step '{step.get('name', tool_name)}': {res.message}",
                    data={"steps_completed": results},
                )

        return ExecutionResult.completed(data={"pipeline_results": results}, message="Tool pipeline completed successfully.")
