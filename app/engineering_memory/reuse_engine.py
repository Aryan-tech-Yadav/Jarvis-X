"""Deterministic component and code reuse recommendations."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .code_knowledge_base import CodeKnowledgeBase


@dataclass
class ReuseMatch:
    path: str
    score: float
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"path": self.path, "score": self.score, "reasons": list(self.reasons)}


class ReuseEngine:
    def __init__(self, code_base: CodeKnowledgeBase | None = None):
        self.code_base = code_base or CodeKnowledgeBase()

    def find(self, features=None, dependencies=None, limit: int = 5) -> List[ReuseMatch]:
        wanted_features = {str(item).casefold() for item in (features or [])}
        wanted_dependencies = {str(item).casefold() for item in (dependencies or [])}
        matches = []
        for item in self.code_base.all():
            item_features = {str(value).casefold() for value in item.features}
            item_dependencies = {str(value).casefold() for value in item.dependencies}
            feature_overlap = len(wanted_features & item_features)
            dependency_overlap = len(wanted_dependencies & item_dependencies)
            score = (feature_overlap + dependency_overlap) / max(
                1, len(wanted_features) + len(wanted_dependencies)
            )
            if score:
                reasons = []
                if feature_overlap:
                    reasons.append("shared features")
                if dependency_overlap:
                    reasons.append("shared dependencies")
                matches.append(ReuseMatch(item.path, score, reasons))
        matches.sort(key=lambda match: match.score, reverse=True)
        return matches[:max(0, limit)]
