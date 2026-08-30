"""Cognitive Operating System facade; EOS remains an injected executor."""

from typing import Any, Dict, Optional

from .attention import AttentionEngine
from .decision import CognitiveDecisionEngine
from .goals import Goal, GoalStack
from .perception import PerceptionEngine


class CognitiveOperatingSystem:
    def __init__(self, perception=None, attention=None, decision=None, goals=None, event_bus=None):
        self.perception = perception or PerceptionEngine()
        self.attention = attention or AttentionEngine()
        self.decision = decision or CognitiveDecisionEngine()
        self.goals = goals or GoalStack()
        self.event_bus = event_bus

    def understand(self, input_value: Any, source: str = "user",
                   context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        perception = self.perception.perceive(input_value, source)
        goal_text = input_value if isinstance(input_value, str) else str(input_value)
        decision = self.decision.decide(goal_text, context)
        goal = self.goals.add(Goal(goal_text, priority=int((context or {}).get("priority", 2))))
        result = {"perception": perception.to_dict(), "decision": decision.to_dict(),
                  "goal": goal.to_dict()}
        if self.event_bus is not None:
            self.event_bus.publish("COGNITION_COMPLETED", result)
        return result

