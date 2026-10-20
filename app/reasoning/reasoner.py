"""Composable reasoning coordinator with explainable decision metadata."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .critic import Critic
from .memory_reasoner import MemoryReasoner
from .planner import Planner
from .reflector import Reflector
from .validator import Validator


@dataclass
class ReasoningDecision:
    goal: str
    plan: Dict[str, Any]
    critique: Dict[str, Any]
    validation: Dict[str, Any]
    reflection: Optional[Dict[str, Any]] = None
    result: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


class Reasoner:
    """Run Plan -> Critique -> Validate -> Execute -> Reflect."""

    def __init__(self, planner=None, critic=None, validator=None, reflector=None,
                 memory_reasoner=None, event_bus=None):
        self.planner = planner or Planner()
        self.critic = critic or Critic()
        self.validator = validator or Validator()
        self.reflector = reflector or Reflector()
        self.memory_reasoner = memory_reasoner or MemoryReasoner()
        self.event_bus = event_bus

    def reason(self, goal: str, execute=None, context: Optional[Dict[str, Any]] = None) -> ReasoningDecision:
        context = dict(context or {})
        context["memory"] = self.memory_reasoner.recall(goal)
        plan = self.planner.create(goal, context)
        critique = self.critic.review(plan, context)
        validation = self.validator.validate(plan)
        if not critique.approved:
            validation.valid = False
            validation.errors.extend(critique.issues)
        result = None
        reflection = None
        if validation.valid and execute is not None:
            result = execute(plan)
            result_validation = self.validator.validate(result)
            validation.errors.extend(result_validation.errors)
            validation.warnings.extend(result_validation.warnings)
            validation.valid = validation.valid and result_validation.valid
            reflection = self.reflector.reflect(goal, result).to_dict()
            self.memory_reasoner.learn(goal, reflection)
        decision = ReasoningDecision(goal, plan.to_dict(), critique.to_dict(),
                                     validation.to_dict(), reflection, result)
        if self.event_bus is not None:
            self.event_bus.publish("REASONING_COMPLETED", decision.to_dict())
        return decision

