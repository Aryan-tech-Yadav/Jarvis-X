"""Transparent strategy candidate selector."""

from typing import Any, Dict, List


class StrategySelector:
    def rank(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(candidates, key=lambda item: (
            -float(item.get("score", 0.0)),
            float(item.get("risk", 1.0)),
            int(item.get("estimated_minutes", 0)),
            str(item.get("name", "")).casefold(),
        ))

    def select(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any] | None:
        ranked = self.rank(candidates)
        return ranked[0] if ranked else None

