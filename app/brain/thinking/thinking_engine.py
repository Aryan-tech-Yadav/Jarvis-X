"""Thinking Engine - Core reasoning module.

Week 1: Thinking Engine
Har request pe:
  Problem -> Understand -> Break into sub-problems -> Generate 3 plans -> Score -> Select best

Target:
  - Jarvis kabhi direct answer na de
  - Hamesha planning kare
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

from app.core.logger import Logger
from app.brain.utils import emit_event, extract_json


class ThinkingMode(str, Enum):
    """Thinking modes for different task complexities."""
    FAST = "fast"  # Simple commands, no planning needed
    DEEP = "deep"  # Complex tasks, full reasoning
    CREATIVE = "creative"  # Architecture/design tasks
    DEBUG = "debug"  # Error analysis
    RESEARCH = "research"  # Information gathering


@dataclass
class SubProblem:
    """A decomposed sub-problem."""
    sub_problem_id: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    estimated_effort: str = "medium"
    required_tools: List[str] = field(default_factory=list)


@dataclass
class Plan:
    """A complete plan for solving a problem."""
    plan_id: str
    description: str
    steps: List[str]
    estimated_time: float = 0.0
    confidence: float = 0.0
    risk: float = 0.0
    required_tools: List[str] = field(default_factory=list)
    sub_problems: List[SubProblem] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThinkingResult:
    """Result of thinking process."""
    original_problem: str
    thinking_mode: ThinkingMode
    understanding: str
    sub_problems: List[SubProblem]
    plans: List[Plan]
    selected_plan: Optional[Plan]
    reasoning: str
    confidence: float
    duration: float = 0.0


class ThinkingEngine:
    """Core thinking engine for problem decomposition and planning.

    This is the brain's cortex - it never gives direct answers.
    Every request goes through: Understand -> Decompose -> Plan -> Select
    """

    def __init__(self, ai_router=None, event_bus=None):
        self.ai_router = ai_router
        self.event_bus = event_bus
        self._thinking_history: List[ThinkingResult] = []

    def think(self, problem: str, context: Dict[str, Any] = None) -> ThinkingResult:
        """Main thinking pipeline.

        Args:
            problem: User's request/problem
            context: Additional context (memory, user profile, etc.)

        Returns:
            ThinkingResult with decomposition, plans, and selection
        """
        start_time = time.perf_counter()
        context = context or {}

        # Determine thinking mode
        mode = self._determine_thinking_mode(problem, context)
        Logger.info(f"[Thinking] Mode: {mode.value} for: {problem[:50]}...")

        # Step 1: Understand
        understanding = self._understand(problem, context)
        emit_event(self.event_bus, "THINKING_UNDERSTOOD", {"understanding": understanding})

        # Step 2: Decompose
        sub_problems = self._decompose(problem, understanding, context)
        emit_event(self.event_bus, "THINKING_DECOMPOSED", {"sub_problems": len(sub_problems)})

        # Step 3: Generate plans
        plans = self._generate_plans(problem, understanding, sub_problems, context, mode)
        emit_event(self.event_bus, "THINKING_PLANS_GENERATED", {"plans": len(plans)})

        # Step 4: Score plans
        scored_plans = self._score_plans(plans, context)
        emit_event(self.event_bus, "THINKING_PLANS_SCORED", {"scores": [p.confidence for p in scored_plans]})

        # Step 5: Select best plan
        selected_plan, reasoning = self._select_plan(scored_plans, context)
        confidence = selected_plan.confidence if selected_plan else 0.0

        duration = time.perf_counter() - start_time

        result = ThinkingResult(
            original_problem=problem,
            thinking_mode=mode,
            understanding=understanding,
            sub_problems=sub_problems,
            plans=scored_plans,
            selected_plan=selected_plan,
            reasoning=reasoning,
            confidence=confidence,
            duration=duration,
        )

        self._thinking_history.append(result)
        emit_event(self.event_bus, "THINKING_COMPLETED", {
            "mode": mode.value,
            "confidence": confidence,
            "plans_generated": len(plans),
            "duration": duration,
        })

        return result

    def _determine_thinking_mode(self, problem: str, context: Dict[str, Any]) -> ThinkingMode:
        """Determine appropriate thinking mode."""
        problem_lower = problem.lower()

        # Simple patterns
        simple_patterns = ["hello", "hi", "hey", "what time", "status", "help"]
        if any(p in problem_lower for p in simple_patterns):
            return ThinkingMode.FAST

        # Debug patterns
        debug_patterns = ["error", "fix", "debug", "issue", "broken", "failing"]
        if any(p in problem_lower for p in debug_patterns):
            return ThinkingMode.DEBUG

        # Research patterns
        research_patterns = ["search", "find", "research", "look up", "what is"]
        if any(p in problem_lower for p in research_patterns):
            return ThinkingMode.RESEARCH

        # Architecture patterns
        arch_patterns = ["design", "architect", "build", "create", "develop", "implement"]
        if any(p in problem_lower for p in arch_patterns):
            return ThinkingMode.DEEP

        return ThinkingMode.DEEP

    def _understand(self, problem: str, context: Dict[str, Any]) -> str:
        """Understand the problem."""
        if self.ai_router:
            try:
                prompt = f"""Understand this problem in 1-2 sentences.

Problem: {problem}

Context: {json.dumps(context.get('memories', []))[:500]}

Understanding:"""
                understanding = self.ai_router.ask(prompt, task_type="thinking")
                return understanding.strip()
            except Exception:
                pass

        return f"User wants to: {problem}"

    def _decompose(self, problem: str, understanding: str, context: Dict[str, Any]) -> List[SubProblem]:
        """Break problem into sub-problems."""
        if self.ai_router:
            try:
                prompt = f"""Break this into 2-4 sub-problems.

Problem: {problem}
Understanding: {understanding}

Return JSON array:
[{{"description": "...", "dependencies": [], "effort": "medium", "tools": []}}]

JSON:"""
                response = self.ai_router.ask(prompt, task_type="thinking")
                json_match = extract_json(response)
                if json_match:
                    data = json.loads(json_match)
                    return [
                        SubProblem(
                            sub_problem_id=f"sp_{i+1}",
                            description=item.get("description", ""),
                            dependencies=item.get("dependencies", []),
                            estimated_effort=item.get("effort", "medium"),
                            required_tools=item.get("tools", []),
                        )
                        for i, item in enumerate(data)
                    ]
            except Exception:
                pass

        return [SubProblem(sub_problem_id="sp_1", description=problem, estimated_effort="medium")]

    def _generate_plans(self, problem: str, understanding: str, sub_problems: List[SubProblem],
                        context: Dict[str, Any], mode: ThinkingMode) -> List[Plan]:
        """Generate 3 possible plans."""
        plans = []

        if self.ai_router:
            try:
                prompt = f"""Generate 3 different plans to solve this problem.

Problem: {problem}
Understanding: {understanding}
Mode: {mode.value}

For each plan, provide:
- description
- steps (array of strings)
- estimated_time (seconds)
- confidence (0-100)
- risk (0-100)
- required_tools (array)

Return JSON array of 3 plans:
[{{"description": "...", "steps": [...], "estimated_time": 60, "confidence": 90, "risk": 20, "required_tools": []}}]

JSON:"""
                response = self.ai_router.ask(prompt, task_type="thinking")
                json_match = extract_json(response)
                if json_match:
                    data = json.loads(json_match)
                    for i, item in enumerate(data[:3]):
                        plans.append(Plan(
                            plan_id=f"plan_{i+1}",
                            description=item.get("description", ""),
                            steps=item.get("steps", []),
                            estimated_time=item.get("estimated_time", 0.0),
                            confidence=item.get("confidence", 0.0),
                            risk=item.get("risk", 0.0),
                            required_tools=item.get("required_tools", []),
                            sub_problems=sub_problems,
                        ))
            except Exception:
                pass

        if not plans:
            plans = self._generate_fallback_plans(problem, sub_problems)

        return plans

    def _generate_fallback_plans(self, problem: str, sub_problems: List[SubProblem]) -> List[Plan]:
        """Generate fallback plans without AI."""
        return [
            Plan(
                plan_id="plan_1",
                description=f"Direct approach: {problem}",
                steps=[f"Execute: {sp.description}" for sp in sub_problems],
                estimated_time=30.0,
                confidence=70.0,
                risk=30.0,
                sub_problems=sub_problems,
            ),
            Plan(
                plan_id="plan_2",
                description=f"Research-first approach for: {problem}",
                steps=["Research existing solutions", "Analyze best approach", f"Execute: {problem}"],
                estimated_time=60.0,
                confidence=80.0,
                risk=20.0,
                sub_problems=sub_problems,
            ),
            Plan(
                plan_id="plan_3",
                description=f"Test-first approach for: {problem}",
                steps=["Create tests", f"Implement: {problem}", "Validate"],
                estimated_time=90.0,
                confidence=85.0,
                risk=15.0,
                sub_problems=sub_problems,
            ),
        ]

    def _score_plans(self, plans: List[Plan], context: Dict[str, Any]) -> List[Plan]:
        """Score each plan based on multiple factors."""
        for plan in plans:
            # Base score from confidence
            score = plan.confidence

            # Penalize risk
            score -= plan.risk * 0.5

            # Penalize time
            if plan.estimated_time > 300:
                score -= 10
            elif plan.estimated_time > 120:
                score -= 5

            # Bonus for having required tools available
            available_tools = context.get("available_tools", [])
            tool_match = sum(1 for tool in plan.required_tools if tool in available_tools)
            score += tool_match * 5

            plan.confidence = max(0.0, min(100.0, score))

        return sorted(plans, key=lambda p: p.confidence, reverse=True)

    def _select_plan(self, plans: List[Plan], context: Dict[str, Any]) -> tuple[Optional[Plan], str]:
        """Select best plan and provide reasoning."""
        if not plans:
            return None, "No plans generated"

        best = plans[0]
        reasoning = f"Selected Plan {best.plan_id}: {best.description} (confidence: {best.confidence:.0f}%, risk: {best.risk:.0f}%)"

        if len(plans) > 1:
            reasoning += f". Runner-up: {plans[1].plan_id} ({plans[1].confidence:.0f}%)"

        return best, reasoning

    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON from text."""
        import re
        json_match = re.search(r"\[.*\]", text, re.DOTALL)
        if json_match:
            return json_match.group()
        return None

    def get_history(self) -> List[ThinkingResult]:
        """Get thinking history."""
        return list(self._thinking_history)
