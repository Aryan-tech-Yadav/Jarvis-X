"""Adaptive strategy facade over the existing strategy evaluator."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.strategy.strategy_engine import StrategyEngine

from .strategy_registry import StrategyRegistry
from .strategy_selector import StrategySelector


@dataclass
class StrategyDecision:
    goal: str
    selected: Dict[str, Any]
    alternatives: list[Dict[str, Any]]
    context: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {"goal": self.goal, "selected": dict(self.selected),
                "alternatives": [dict(item) for item in self.alternatives],
                "context": dict(self.context)}


class StrategyManager:
    def __init__(self, engine: Optional[StrategyEngine] = None,
                 registry: Optional[StrategyRegistry] = None,
                 selector: Optional[StrategySelector] = None,
                 event_bus=None):
        self.engine = engine or StrategyEngine()
        self.registry = registry or StrategyRegistry()
        self.selector = selector or StrategySelector()
        self.event_bus = event_bus

    def choose(self, goal: str, context: Optional[Dict[str, Any]] = None) -> StrategyDecision:
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("Goal cannot be empty")
        project_context = dict(context or {})
        project_context.setdefault("goal", goal.strip())
        candidates = [strategy.describe(project_context)
                      for strategy in self.registry.matching(project_context)]
        if candidates:
            evaluated = [self.engine.evaluator.evaluate(item, goal, self.engine.history.experience(item["name"], goal))
                         for item in candidates]
            result = [item.to_dict() for item in evaluated]
            selected = self.selector.select(result)
            alternatives = self.selector.rank(result)
        else:
            result = self.engine.choose(goal)
            selected = result["selected"]
            alternatives = result["alternatives"]
        decision = StrategyDecision(goal.strip(), selected or {}, alternatives, project_context)
        if self.event_bus is not None:
            self.event_bus.publish("STRATEGY_SELECTED", decision.to_dict())
        return decision

