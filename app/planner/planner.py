"""Planner module - Goal decomposition and execution planning.

Layer 3 of the 5-layer AI Agent architecture.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PlanStep:
    """Single step in an execution plan."""
    step_id: str
    description: str
    tool: Optional[str] = None
    action: Optional[str] = None
    arguments: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    estimated_effort: str = "low"
    status: str = "pending"
    result: Optional[str] = None


@dataclass
class ExecutionPlan:
    """Complete execution plan."""
    goal: str
    intent: str
    steps: List[PlanStep]
    total_effort: str = "low"
    can_parallelize: bool = False
    requires_clarification: bool = False
    clarification_questions: List[str] = field(default_factory=list)


class Planner:
    """Goal decomposition and execution planning.

    Transforms user intent into structured, executable plans.
    Supports:
      - Simple task decomposition
      - Dependency analysis
      - Parallel step identification
      - Effort estimation
    """

    # Intent-specific plan templates
    PLAN_TEMPLATES = {
        "CREATE_CODE": [
            "Analyze requirement and determine project structure",
            "Select technology stack and design patterns",
            "Generate project files and code",
            "Run tests and QA checks",
            "Fix any errors and finalize",
        ],
        "GOOGLE_SEARCH": [
            "Parse search query from user input",
            "Execute web search",
            "Summarize results for user",
        ],
        "OPEN_APPLICATION": [
            "Extract application name from input",
            "Launch or focus the application",
        ],
        "OPEN_WEBSITE": [
            "Extract website name from input",
            "Open website in default browser",
        ],
        "GET_NEWS": [
            "Determine news category from input",
            "Fetch latest news headlines",
            "Present summary to user",
        ],
        "PLAY_MUSIC": [
            "Extract song/service name from input",
            "Launch music service",
            "Play requested content",
        ],
        "WEATHER": [
            "Extract location from input",
            "Fetch weather data",
            "Present weather summary",
        ],
        "WIKIPEDIA": [
            "Extract topic from input",
            "Fetch Wikipedia summary",
            "Present information to user",
        ],
        "CHAT": [
            "Understand user question",
            "Retrieve relevant context from memory",
            "Generate helpful response",
        ],
        "SAVE_MEMORY": [
            "Extract key-value pair from input",
            "Store in persistent memory",
            "Confirm storage to user",
        ],
        "GET_MEMORY": [
            "Extract query key from input",
            "Search memory for matching entry",
            "Return stored value",
        ],
    }

    def __init__(self, ai_router=None):
        self.ai_router = ai_router

    def plan(self, user_input: str, intent: str, entities: Dict[str, Any] = None) -> List[str]:
        """Create execution plan for given input.

        Args:
            user_input: Raw user input
            intent: Detected intent
            entities: Extracted entities

        Returns:
            List of plan step descriptions
        """
        entities = entities or {}

        if intent in self.PLAN_TEMPLATES:
            steps = self._adapt_template(intent, user_input, entities)
            if steps:
                return steps

        return self._decompose_general(user_input, intent)

    def _adapt_template(self, intent: str, user_input: str, entities: Dict[str, Any]) -> List[str]:
        """Adapt a plan template to specific user input."""
        template = self.PLAN_TEMPLATES.get(intent, [])
        adapted = []

        for step in template:
            adapted.append(self._personalize_step(step, user_input, entities))

        return adapted

    def _personalize_step(self, step: str, user_input: str, entities: Dict[str, Any]) -> str:
        """Personalize a plan step with specific details from input."""
        if "{query}" in step and entities.get("query"):
            return step.replace("{query}", entities["query"])
        if "{app}" in step and entities.get("app_name"):
            return step.replace("{app}", entities["app_name"])
        if "{song}" in step and entities.get("song_name"):
            return step.replace("{song}", entities["song_name"])
        if "{location}" in step and entities.get("location"):
            return step.replace("{location}", entities["location"])
        if "{project}" in step and entities.get("project_name"):
            return step.replace("{project}", entities["project_name"])
        return step

    def _decompose_general(self, user_input: str, intent: str) -> List[str]:
        """Decompose general tasks using LLM or heuristics."""
        if self.ai_router:
            try:
                prompt = f"""Break this user request into 3-5 clear steps:
User: {user_input}
Intent: {intent}

Return only a numbered list of steps, one per line."""
                response = self.ai_router.ask(prompt, task_type="planning")
                steps = self._parse_numbered_list(response)
                if steps:
                    return steps
            except Exception:
                pass

        return [
            f"Process request: {user_input[:50]}",
            f"Execute action for intent: {intent}",
            f"Return result to user",
        ]

    def _parse_numbered_list(self, text: str) -> List[str]:
        """Parse numbered list from LLM response."""
        steps = []
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            if line[0].isdigit() and len(line) > 2 and line[1] in ".): ":
                steps.append(line[2:].strip())
            elif line.startswith("-"):
                steps.append(line[1:].strip())
        return steps if steps else []

    def get_structured_plan(self, user_input: str, intent: str, entities: Dict[str, Any] = None) -> ExecutionPlan:
        """Get a structured execution plan with metadata."""
        steps = self.plan(user_input, intent, entities)
        plan_steps = [
            PlanStep(
                step_id=f"step_{i+1}",
                description=step,
                tool=self._infer_tool(step, intent),
                action=self._infer_action(step),
            )
            for i, step in enumerate(steps)
        ]

        total_effort = "high" if len(plan_steps) > 5 else "medium" if len(plan_steps) > 3 else "low"
        can_parallelize = len(plan_steps) > 1 and intent in ["GET_NEWS", "WEATHER"]

        return ExecutionPlan(
            goal=user_input,
            intent=intent,
            steps=plan_steps,
            total_effort=total_effort,
            can_parallelize=can_parallelize,
        )

    def _infer_tool(self, step: str, intent: str) -> Optional[str]:
        """Infer which tool is needed for a step."""
        step_lower = step.lower()
        if any(w in step_lower for w in ["search", "google", "web"]):
            return "internet"
        if any(w in step_lower for w in ["app", "application", "open"]):
            return "automation"
        if any(w in step_lower for w in ["file", "save", "generate"]):
            return "file"
        if any(w in step_lower for w in ["code", "python", "run"]):
            return "python"
        if any(w in step_lower for w in ["music", "play", "song"]):
            return "media"
        if any(w in step_lower for w in ["remember", "memory", "store"]):
            return "memory"
        return "ai"

    def _infer_action(self, step: str) -> Optional[str]:
        """Infer action name for a step."""
        step_lower = step.lower()
        if "extract" in step_lower or "parse" in step_lower:
            return "extract"
        if "fetch" in step_lower or "search" in step_lower:
            return "search"
        if "generate" in step_lower or "create" in step_lower:
            return "create"
        if "open" in step_lower or "launch" in step_lower:
            return "open"
        if "run" in step_lower or "execute" in step_lower:
            return "execute"
        if "present" in step_lower or "return" in step_lower or "summarize" in step_lower:
            return "summarize"
        return "process"
