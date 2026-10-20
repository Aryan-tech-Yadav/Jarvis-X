"""Tool selector - LLM-driven tool selection.

Layer 5 of the 5-layer AI Agent architecture.
Uses the LLM to intelligently select and parameterize tools.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.core.logger import Logger


@dataclass
class ToolSelection:
    """Result of tool selection."""
    tool_name: str
    action: Optional[str]
    arguments: Dict[str, Any]
    confidence: float
    reasoning: str = ""


class ToolSelector:
    """Intelligently select tools based on user intent and context.

    Uses LLM reasoning to choose the best tool for a given task,
    falling back to rule-based selection if LLM is unavailable.
    """

    def __init__(self, tool_registry=None, ai_router=None, registry=None):
        # ``registry`` is the short-form used by the universal tool facade.
        self.tool_registry = tool_registry or registry
        self.ai_router = ai_router
        self._tool_catalog: Dict[str, Dict[str, Any]] = {}

    def initialize(self):
        """Build tool catalog from registry."""
        if self.tool_registry is None:
            try:
                from app.tools.tool_registry import ToolRegistry
                self.tool_registry = ToolRegistry()
            except Exception:
                pass

        if self.ai_router is None:
            try:
                from app.llm.llm_router import LLMRouter
                self.ai_router = LLMRouter()
            except Exception:
                pass

        self._build_catalog()

    def _build_catalog(self):
        """Build internal catalog of available tools."""
        if not self.tool_registry:
            return

        for tool in self.tool_registry.list():
            meta = tool.metadata
            self._tool_catalog[meta.name] = {
                "name": meta.name,
                "description": meta.description,
                "tags": meta.tags or [],
                "actions": meta.actions or [],
                "permissions": meta.permissions or [],
            }

    def select(
        self,
        intent: str,
        user_input: str = "",
        plan: List[str] = None,
        action: Optional[str] = None,
    ):
        """Select the best matching tool, respecting capability and priority."""

        if self.tool_registry is not None:
            try:
                tools = list(self.tool_registry.list())
            except (AttributeError, TypeError):
                tools = []

            query = f"{intent or ''} {user_input or ''}".lower()
            query_terms = set(query.replace("-", " ").replace("_", " ").split())
            requested_action = action.lower() if action else None
            ranked = []

            for tool in tools:
                meta = getattr(tool, "metadata", tool)

                name = str(getattr(meta, "name", ""))
                description = str(getattr(meta, "description", ""))
                actions = list(getattr(meta, "actions", []) or [])
                tags = list(getattr(meta, "tags", []) or [])
                priority = getattr(meta, "priority", 0) or 0

                normalized_actions = [str(a).lower() for a in actions]

                if requested_action and requested_action not in normalized_actions:
                    continue

                searchable = " ".join(
                    [name, description] + [str(x) for x in actions + tags]
                ).lower().replace("-", " ").replace("_", " ")

                searchable_terms = set(searchable.split())
                overlap = len(query_terms & searchable_terms)

                # Prefer relevant tools, then use priority to break ties.
                score = overlap * 10 + float(priority) * 0.1

                if requested_action:
                    score += 100

                if name.lower().replace("-", " ") in query:
                    score += 5

                if overlap or requested_action:
                    ranked.append((score, tool))

            if ranked:
                return max(ranked, key=lambda item: item[0])[1]

            # Preserve the registry API: no matching tool means None.
            return None

        rule_based = self._rule_based_selection(intent, user_input)
        if rule_based:
            return rule_based

        if self.ai_router:
            try:
                return self._llm_based_selection(intent, user_input, plan)
            except Exception:
                pass

        return ["ai"]

    def select_detailed(self, intent: str, user_input: str, plan: List[str] = None) -> List[ToolSelection]:
        """Select tools with detailed arguments using LLM reasoning."""
        selections = []

        # Rule-based first
        rule_tools = self._rule_based_selection(intent, user_input)
        if rule_tools:
            for tool_name in rule_tools:
                selections.append(ToolSelection(
                    tool_name=tool_name,
                    action=self._infer_action(intent, tool_name),
                    arguments=self._infer_arguments(intent, user_input, tool_name),
                    confidence=0.8,
                    reasoning="Rule-based selection",
                ))
            return selections

        # LLM-based
        if self.ai_router:
            try:
                llm_result = self._llm_select_detailed(intent, user_input, plan)
                selections.extend(llm_result)
                return selections
            except Exception:
                pass

        return [ToolSelection("ai", "ask", {"prompt": user_input}, 0.5, "Default fallback")]

    def _rule_based_selection(self, intent: str, user_input: str) -> List[str]:
        """Rule-based tool selection for known intents."""
        intent_tools = {
            "OPEN_APPLICATION": ["automation"],
            "CLOSE_APPLICATION": ["automation"],
            "OPEN_WEBSITE": ["automation"],
            "OPEN_FOLDER": ["automation"],
            "GOOGLE_SEARCH": ["internet"],
            "GET_NEWS": ["internet"],
            "WEATHER": ["internet"],
            "WIKIPEDIA": ["internet"],
            "PLAY_MUSIC": ["automation", "media"],
            "PLAY_SPOTIFY_SONG": ["automation", "media"],
            "CREATE_CODE": ["file", "python", "terminal"],
            "SAVE_MEMORY": ["memory"],
            "GET_MEMORY": ["memory"],
            "GET_TIME": [],
            "SHUTDOWN": ["automation"],
            "RESTART": ["automation"],
            "SLEEP": ["automation"],
            "LOCK": ["automation"],
            "STATUS": [],
            "HELP": [],
            "EXIT": [],
            "HISTORY": ["memory"],
        }
        return intent_tools.get(intent, ["ai"])

    def _infer_action(self, intent: str, tool_name: str) -> Optional[str]:
        """Infer action name from intent and tool."""
        intent_action_map = {
            "OPEN_APPLICATION": "open_application",
            "CLOSE_APPLICATION": "close_application",
            "OPEN_WEBSITE": "open_website",
            "GOOGLE_SEARCH": "search",
            "GET_NEWS": "get_news",
            "WEATHER": "get_weather",
            "PLAY_MUSIC": "play_music",
            "CREATE_CODE": "generate",
        }
        return intent_action_map.get(intent, "process")

    def _infer_arguments(self, intent: str, user_input: str, tool_name: str) -> Dict[str, Any]:
        """Infer arguments for tool from user input."""
        args = {"input": user_input}
        if tool_name == "automation":
            args["command"] = user_input
        elif tool_name == "internet":
            args["query"] = user_input
        elif tool_name == "ai":
            args["prompt"] = user_input
        return args

    def _llm_based_selection(self, intent: str, user_input: str, plan: List[str] = None) -> List[str]:
        """Use LLM to select tools dynamically."""
        tool_list = ", ".join(self._tool_catalog.keys()) or "ai, automation, internet, file, python"
        plan_text = "\n".join(f"- {s}" for s in (plan or [])) or "No plan available"

        prompt = f"""Given the user request and execution plan, select the most appropriate tools.

Available tools: {tool_list}

User intent: {intent}
User input: {user_input}
Plan:
{plan_text}

Return ONLY a comma-separated list of tool names that are needed.
Example: automation, ai

Tools:"""

        response = self.ai_router.ask(prompt, task_type="tool_selection").strip()
        tools = [t.strip() for t in response.split(",") if t.strip()]
        return [t for t in tools if t in self._tool_catalog] or ["ai"]

    def _llm_select_detailed(self, intent: str, user_input: str, plan: List[str] = None) -> List[ToolSelection]:
        """Use LLM to select tools with detailed arguments."""
        tools_summary = "\n".join(
            f"- {name}: {info['description']}" for name, info in self._tool_catalog.items()
        ) or "- ai: General conversation"

        prompt = f"""Select tools for this request. Return JSON array.

Available tools:
{tools_summary}

User intent: {intent}
User input: {user_input}

Return JSON array of objects with: tool_name, action, arguments (object), confidence (0-1), reasoning.

JSON:"""

        try:
            response = self.ai_router.ask(prompt, task_type="tool_selection")
            import json
            data = json.loads(response)
            if isinstance(data, list):
                return [ToolSelection(**item) for item in data]
        except Exception:
            pass

        return []
