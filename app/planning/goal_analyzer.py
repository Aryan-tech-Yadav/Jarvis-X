"""Structured analysis of a natural-language engineering goal."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from app.engineering.requirement_analyzer import RequirementAnalysis, RequirementAnalyzer


@dataclass
class GoalAnalysis:
    goal: str
    difficulty: str
    estimated_hours: int
    project_type: str
    technologies: List[str]
    deliverables: List[str]
    requirements: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data.pop("requirements", None)
        return data


class GoalAnalyzer:
    """Convert a goal into stable planning facts without requiring an LLM."""

    _BASE_DELIVERABLES = ("Tests", "README")

    def __init__(self, analyzer: Optional[RequirementAnalyzer] = None):
        self.analyzer = analyzer or RequirementAnalyzer()

    def analyze(self, goal: str) -> GoalAnalysis:
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("Goal cannot be empty")

        analysis = self.analyzer.analyze(goal.strip())
        project_name = analysis.project_name
        for article in ("a ", "an ", "the "):
            if project_name.lower().startswith(article):
                project_name = project_name[len(article):]
                break
        deliverables = self._deliverables(analysis)
        technologies = self._technologies(analysis)
        complexity = len(deliverables) + len(analysis.modules) + len(analysis.roles)
        difficulty = "High" if complexity >= 10 else "Medium" if complexity >= 6 else "Low"

        return GoalAnalysis(
            goal=project_name,
            difficulty=difficulty,
            estimated_hours=max(2, complexity * 2),
            project_type=analysis.project_type.title(),
            technologies=technologies,
            deliverables=deliverables,
            requirements=analysis.to_dict(),
        )

    @staticmethod
    def _technologies(analysis: RequirementAnalysis) -> List[str]:
        values = [
            analysis.backend,
            analysis.frontend,
            analysis.database,
            analysis.cache,
            analysis.queue,
            analysis.storage,
            analysis.monitoring,
        ]
        return list(dict.fromkeys(value for value in values if value and value != "None"))

    def _deliverables(self, analysis: RequirementAnalysis) -> List[str]:
        deliverables = []
        if analysis.backend:
            deliverables.append("Backend")
        if analysis.frontend:
            deliverables.append("Frontend")
        if analysis.database and analysis.database != "None":
            deliverables.append("Database")
        if "deployment" in analysis.missing_information or analysis.project_type in {"web", "api"}:
            deliverables.append("Docker")
        deliverables.extend(self._BASE_DELIVERABLES)
        return list(dict.fromkeys(deliverables))
