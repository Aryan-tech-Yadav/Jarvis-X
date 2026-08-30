"""Tool ranker.

Ranks tools by relevance, success rate, and priority.
"""

from __future__ import annotations

import re
from typing import Any


class ToolRanker:
    def score(self, tool, request, history=None):
        name = self._value(tool, "name")
        description = self._value(tool, "description")
        terms = set(re.findall(r"[a-z0-9_]+", str(request).casefold()))
        searchable = set(re.findall(r"[a-z0-9_]+", f"{name} {description}".casefold()))
        matches = len(terms & searchable)
        stats = (history or {}).get(name, {})
        success_rate = float(stats.get("success_rate", 0.5))
        priority = float(self._value(tool, "priority", 0))
        return matches * 10 + success_rate * 3 + priority / 100

    def rank(self, tools, request, history=None):
        return sorted(tools, key=lambda tool: self.score(tool, request, history), reverse=True)

    @staticmethod
    def _value(tool, key, default=""):
        if isinstance(tool, dict):
            return tool.get(key, default)
        # BaseTool instances store metadata in .metadata
        if hasattr(tool, "metadata") and tool.metadata is not None and hasattr(tool.metadata, key):
            return getattr(tool.metadata, key)
        return getattr(tool, key, default)
