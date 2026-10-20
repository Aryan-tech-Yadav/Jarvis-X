"""Adaptive cognitive orchestration without directly executing side effects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.intelligence.strategy.strategy_manager import StrategyManager
from app.reasoning.confidence_router import ConfidenceRouter
from app.reasoning.planner import Planner
from app.reasoning.tree_of_thought import ThoughtTreeResult, TreeOfThoughtEngine

from .decision import CognitiveDecisionEngine
from .perception import PerceptionEngine


@dataclass(frozen=True)
class WorkingMemory:
    """Small, explicit context passed between cognitive stages."""

    goal: str
    known_facts: List[str] = field(default_factory=list)
    unknowns: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "known_facts": list(self.known_facts),
            "unknowns": list(self.unknowns),
            "risks": list(self.risks),
            "constraints": list(self.constraints),
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class CognitivePlan:
    """Adaptive plan selected before any execution system is invoked."""

    goal: str
    depth: str
    thinking_mode: str
    thinking_budget_ms: int
    action: str
    route: str
    agents: List[str]
    mental_models: List[str]
    research_required: bool
    verification_required: bool
    simulation_required: bool
    working_memory: WorkingMemory
    plan: Dict[str, Any]
    strategy: Dict[str, Any]
    thought_tree: ThoughtTreeResult

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "goal": self.goal,
            "depth": self.depth,
            "thinking_mode": self.thinking_mode,
            "thinking_budget_ms": self.thinking_budget_ms,
            "action": self.action,
            "route": self.route,
            "agents": list(self.agents),
            "mental_models": list(self.mental_models),
            "research_required": self.research_required,
            "verification_required": self.verification_required,
            "simulation_required": self.simulation_required,
            "working_memory": self.working_memory.to_dict(),
            "plan": dict(self.plan),
            "strategy": dict(self.strategy),
            "thought_tree": self.thought_tree.to_dict(),
        }
        return result


class CognitiveOrchestrator:
    """Choose thinking depth and safeguards from the request and context."""

    def __init__(
        self,
        *,
        perception: Optional[PerceptionEngine] = None,
        decisions: Optional[CognitiveDecisionEngine] = None,
        planner: Optional[Planner] = None,
        strategies: Optional[StrategyManager] = None,
        confidence_router: Optional[ConfidenceRouter] = None,
        thought_engine: Optional[TreeOfThoughtEngine] = None,
    ):
        self.perception = perception or PerceptionEngine()
        self.decisions = decisions or CognitiveDecisionEngine()
        self.planner = planner or Planner()
        self.strategies = strategies or StrategyManager()
        self.confidence_router = confidence_router or ConfidenceRouter()
        self.thought_engine = thought_engine or TreeOfThoughtEngine()

    def orchestrate(
        self,
        goal: str,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> CognitivePlan:
        perception = self.perception.perceive(goal)
        values = dict(context or {})
        objective = str(perception.content).strip()
        decision = self.decisions.decide(objective, values)
        thought_tree = self.thought_engine.explore(objective, context=values)
        complexity = self._complexity(objective, values)
        depth = "deep" if complexity >= 3 else "standard" if complexity == 2 else "fast"
        thinking_mode = self._thinking_mode(decision.action, complexity, values)
        thinking_budget_ms = self._thinking_budget(thinking_mode, values)
        confidence = float(values.get("confidence", self._confidence(complexity, decision.confidence)))
        memory = WorkingMemory(
            goal=objective,
            known_facts=list(values.get("known_facts", [])),
            unknowns=list(values.get("unknowns", [])),
            risks=list(values.get("risks", [])),
            constraints=list(values.get("constraints", [])),
            confidence=max(0.0, min(1.0, confidence)),
        )
        models = self._mental_models(objective, decision.action, complexity)
        agents = self._agents(decision.action, complexity)
        research = decision.action == "research" or complexity >= 3 or bool(values.get("research"))
        verification = complexity >= 2 or decision.action in {"research", "ask_user"}
        simulation = bool(values.get("high_risk")) or any(
            word in objective.casefold() for word in ("deploy", "production", "migration", "delete")
        )
        return CognitivePlan(
            goal=objective,
            depth=depth,
            thinking_mode=thinking_mode,
            thinking_budget_ms=thinking_budget_ms,
            action=decision.action,
            route="ask_user" if decision.action == "ask_user"
            else self.confidence_router.route(confidence),
            agents=agents,
            mental_models=models,
            research_required=research,
            verification_required=verification,
            simulation_required=simulation,
            working_memory=memory,
            plan=self.planner.create(objective, values).to_dict(),
            strategy=self.strategies.choose(objective, values).to_dict(),
            thought_tree=thought_tree,
        )

    @staticmethod
    def _complexity(goal: str, context: Dict[str, Any]) -> int:
        score = int(context.get("complexity", 0))
        if len(goal.split()) > 12:
            score += 1
        if any(word in goal.casefold() for word in ("system", "platform", "architecture", "hospital", "banking")):
            score += 1
        if any(word in goal.casefold() for word in ("research", "compare", "production", "deploy")):
            score += 1
        if context.get("high_risk"):
            score += 1
        return min(3, max(1, score))

    @staticmethod
    def _confidence(complexity: int, decision_confidence: float) -> float:
        return max(0.4, min(0.95, decision_confidence - (complexity - 1) * 0.1))

    @staticmethod
    def _thinking_mode(
        action: str,
        complexity: int,
        context: Dict[str, Any],
    ) -> str:
        """Select a bounded thinking mode before planning or execution."""
        requested = context.get("thinking_mode")
        if requested is not None:
            mode = str(requested).strip().upper()
            if mode not in {"FAST", "NORMAL", "DEEP", "EXPERT", "AUTONOMOUS"}:
                raise ValueError(f"Unsupported thinking mode: {requested}")
            return mode
        if context.get("autonomous") or action == "research" and complexity >= 3:
            return "AUTONOMOUS"
        if context.get("expert") or complexity >= 3:
            return "EXPERT"
        if complexity == 2:
            return "NORMAL"
        return "FAST"

    @staticmethod
    def _thinking_budget(mode: str, context: Dict[str, Any]) -> int:
        defaults = {
            "FAST": 200,
            "NORMAL": 5000,
            "DEEP": 30000,
            "EXPERT": 60000,
            "AUTONOMOUS": 120000,
        }
        override = context.get("thinking_budget_ms")
        if override is None:
            return defaults[mode]
        budget = int(override)
        if budget < 1:
            raise ValueError("thinking_budget_ms must be positive")
        return budget

    @staticmethod
    def _mental_models(goal: str, action: str, complexity: int) -> List[str]:
        text = goal.casefold()
        models = []
        if any(word in text for word in ("bug", "error", "failure")):
            models.append("five_whys")
        if any(word in text for word in ("architecture", "system", "platform")):
            models.append("tradeoff_analysis")
        if any(word in text for word in ("optimize", "performance", "latency")):
            models.append("pareto_analysis")
        if action == "research" or complexity >= 3:
            models.append("first_principles")
        return models or ["divide_and_conquer"]

    @staticmethod
    def _agents(action: str, complexity: int) -> List[str]:
        agents = ["planner"]
        if complexity >= 2:
            agents.extend(["architect", "reviewer"])
        if complexity >= 3 or action in {"research", "ask_user"}:
            agents.extend(["researcher", "security", "qa"])
        return agents
