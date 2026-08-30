"""Decision Engine - Score and select best plans.

Week 2: Decision Engine
Har plan ko score kare:
  Plan A: Accuracy: 95, Speed: 80, Risk: 20 -> Overall: 91

Decision reason store kare.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.logger import Logger
from app.brain.utils import emit_event


@dataclass
class DecisionScore:
    """Score for a single plan."""
    plan_id: str
    accuracy: float = 0.0
    speed: float = 0.0
    reliability: float = 0.0
    risk: float = 0.0
    resource_cost: float = 0.0
    overall: float = 0.0
    reasoning: str = ""
    factors: Dict[str, float] = field(default_factory=dict)


@dataclass
class DecisionResult:
    """Result of decision making."""
    selected_plan_id: str
    all_scores: List[DecisionScore]
    reasoning: str
    confidence: float
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class DecisionEngine:
    """Score plans and make decisions.

    Evaluates plans on multiple dimensions:
      - Accuracy: How likely is success?
      - Speed: How fast will it complete?
      - Reliability: How stable is the approach?
      - Risk: What's the failure risk?
      - Resource Cost: How much resources needed?
    """

    def __init__(self, weights: Dict[str, float] = None, event_bus=None):
        self.weights = weights or {
            "accuracy": 0.30,
            "speed": 0.20,
            "reliability": 0.25,
            "risk": 0.15,
            "resource_cost": 0.10,
        }
        self.event_bus = event_bus
        self._decision_history: List[DecisionResult] = []

    def decide(self, plans: List[Any], context: Dict[str, Any] = None) -> DecisionResult:
        """Score plans and select best one.

        Args:
            plans: List of Plan objects from ThinkingEngine
            context: Additional context

        Returns:
            DecisionResult with scores and selection
        """
        start_time = time.perf_counter()
        context = context or {}

        scores = []
        for plan in plans:
            score = self._score_plan(plan, context)
            scores.append(score)

        # Sort by overall score
        scores.sort(key=lambda s: s.overall, reverse=True)

        selected = scores[0] if scores else None
        reasoning = self._generate_reasoning(scores, context)

        duration = time.perf_counter() - start_time

        result = DecisionResult(
            selected_plan_id=selected.plan_id if selected else "",
            all_scores=scores,
            reasoning=reasoning,
            confidence=selected.overall / 100.0 if selected else 0.0,
            duration=duration,
        )

        self._decision_history.append(result)
        self._emit("DECISION_MADE", {
            "selected_plan": selected.plan_id if selected else "",
            "confidence": result.confidence,
            "scores": [{"plan_id": s.plan_id, "overall": s.overall} for s in scores],
        })

        return result

    def _score_plan(self, plan: Any, context: Dict[str, Any]) -> DecisionScore:
        """Score a single plan."""
        factors = {}

        # Accuracy based on plan confidence and historical success
        factors["accuracy"] = self._calculate_accuracy(plan, context)

        # Speed based on estimated time
        factors["speed"] = self._calculate_speed(plan)

        # Reliability based on tools and approach
        factors["reliability"] = self._calculate_reliability(plan, context)

        # Risk (inverted - lower risk is better)
        factors["risk"] = 100.0 - self._calculate_risk(plan, context)

        # Resource cost (inverted - lower cost is better)
        factors["resource_cost"] = 100.0 - self._calculate_resource_cost(plan)

        # Calculate weighted overall score
        overall = sum(factors.get(k, 0.0) * self.weights.get(k, 0.0) for k in self.weights)

        reasoning = self._generate_plan_reasoning(plan, factors, overall)

        return DecisionScore(
            plan_id=plan.plan_id,
            accuracy=factors.get("accuracy", 0.0),
            speed=factors.get("speed", 0.0),
            reliability=factors.get("reliability", 0.0),
            risk=100.0 - factors.get("risk", 100.0),
            resource_cost=100.0 - factors.get("resource_cost", 100.0),
            overall=overall,
            reasoning=reasoning,
            factors=factors,
        )

    def _calculate_accuracy(self, plan: Any, context: Dict[str, Any]) -> float:
        """Calculate accuracy score."""
        # Start with plan's own confidence
        accuracy = getattr(plan, "confidence", 50.0)

        # Boost if plan has successful history
        plan_id = getattr(plan, "plan_id", "")
        history = context.get("plan_history", {}).get(plan_id, {})
        success_rate = history.get("success_rate", 0.5)
        accuracy = accuracy * 0.7 + success_rate * 100 * 0.3

        return min(100.0, max(0.0, accuracy))

    def _calculate_speed(self, plan: Any) -> float:
        """Calculate speed score (higher is better)."""
        estimated_time = getattr(plan, "estimated_time", 60.0)
        # Logarithmic scale: 1s -> 100, 60s -> 70, 300s -> 40
        if estimated_time <= 1:
            return 100.0
        return max(0.0, 100.0 - (estimated_time / 300.0) * 60.0)

    def _calculate_reliability(self, plan: Any, context: Dict[str, Any]) -> float:
        """Calculate reliability score."""
        reliability = 70.0  # Base

        # Boost for well-defined steps
        steps = getattr(plan, "steps", [])
        if len(steps) >= 3:
            reliability += 10.0
        if len(steps) >= 5:
            reliability += 10.0

        # Boost for available tools
        required_tools = getattr(plan, "required_tools", [])
        available_tools = context.get("available_tools", [])
        if required_tools:
            match_rate = sum(1 for t in required_tools if t in available_tools) / len(required_tools)
            reliability += match_rate * 20.0

        return min(100.0, reliability)

    def _calculate_risk(self, plan: Any, context: Dict[str, Any]) -> float:
        """Calculate risk score (higher is riskier)."""
        risk = getattr(plan, "risk", 50.0)

        # Increase risk for complex plans
        steps = getattr(plan, "steps", [])
        if len(steps) > 10:
            risk += 20.0
        elif len(steps) > 5:
            risk += 10.0

        return min(100.0, max(0.0, risk))

    def _calculate_resource_cost(self, plan: Any) -> float:
        """Calculate resource cost (higher is more expensive)."""
        steps = getattr(plan, "steps", [])
        estimated_time = getattr(plan, "estimated_time", 0.0)

        # Simple heuristic
        cost = len(steps) * 5.0 + estimated_time * 0.1
        return min(100.0, cost)

    def _generate_plan_reasoning(self, plan: Any, factors: Dict[str, float], overall: float) -> str:
        """Generate reasoning for plan score."""
        strengths = [k for k, v in factors.items() if v >= 80.0]
        weaknesses = [k for k, v in factors.items() if v <= 40.0]

        parts = [f"Overall score: {overall:.0f}"]
        if strengths:
            parts.append(f"Strengths: {', '.join(strengths)}")
        if weaknesses:
            parts.append(f"Weaknesses: {', '.join(weaknesses)}")

        return ". ".join(parts)

    def _generate_reasoning(self, scores: List[DecisionScore], context: Dict[str, Any]) -> str:
        """Generate overall decision reasoning."""
        if not scores:
            return "No plans to decide"

        best = scores[0]
        parts = [f"Selected {best.plan_id} with score {best.overall:.0f}"]
        parts.append(best.reasoning)

        if len(scores) > 1:
            parts.append(f"Next best: {scores[1].plan_id} ({scores[1].overall:.0f})")

        return ". ".join(parts)

    def _emit(self, event_type: str, payload: Dict[str, Any]):
        """Emit event through event bus."""
        if self.event_bus:
            try:
                self.event_bus.publish(event_type, payload)
            except Exception:
                pass

    def get_decision_history(self) -> List[DecisionResult]:
        """Get decision history."""
        return list(self._decision_history)
