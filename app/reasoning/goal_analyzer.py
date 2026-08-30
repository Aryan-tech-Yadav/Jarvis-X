"""Cognitive goal understanding built on the existing requirement analyzer."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.engineering.requirement_analyzer import RequirementAnalyzer


class GoalAnalyzer:
    def __init__(self, analyzer: Optional[RequirementAnalyzer] = None):
        self.analyzer = analyzer or RequirementAnalyzer()

    def analyze(self, goal: str) -> Dict[str, Any]:
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("Goal cannot be empty")
        result = self.analyzer.analyze(goal.strip())
        project_name = result.project_name
        for article in ("a ", "an ", "the "):
            if project_name.casefold().startswith(article):
                project_name = project_name[len(article):]
                break
        missing = list(result.missing_information)
        return {
            "goal": project_name,
            "domain": result.domain.title(),
            "complexity": self._complexity(result),
            "estimated_time": self._estimated_time(result),
            "missing_information": missing,
            "requirements": result.to_dict(),
        }

    @staticmethod
    def _complexity(result) -> str:
        score = len(result.modules) + len(result.roles) + len(result.missing_information)
        return "High" if score >= 10 else "Medium" if score >= 5 else "Low"

    @staticmethod
    def _estimated_time(result) -> str:
        hours = max(2, (len(result.modules) + len(result.roles)) * 2)
        return f"{hours} Hours"
