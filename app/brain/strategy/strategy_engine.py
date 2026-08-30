"""Strategy Engine - Task-specific execution strategies.

Week 4: Strategy Engine
Jarvis har task ke liye strategy choose kare.

Simple command -> Fast Strategy
Bug fixing -> Debug Strategy
Architecture -> Deep Strategy
Research -> Research Strategy

Hardcoded nahi, rule-based.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from app.core.logger import Logger


class StrategyType(str, Enum):
    """Execution strategies."""
    FAST = "fast"  # Direct execution, no planning
    DEEP = "deep"  # Full planning + execution + verification
    DEBUG = "debug"  # Error analysis + fix + test
    RESEARCH = "research"  # Gather info + synthesize
    CREATIVE = "creative"  # Multiple alternatives + selection
    PARALLEL = "parallel"  # Parallel execution of sub-tasks
    ITERATIVE = "iterative"  # Repeated refinement


@dataclass
class Strategy:
    """Execution strategy."""
    strategy_id: str
    strategy_type: StrategyType
    name: str
    description: str
    steps: List[str]
    required_capabilities: List[str]
    estimated_time: float = 0.0
    confidence: float = 0.0
    success_rate: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyResult:
    """Result of strategy selection."""
    selected_strategy: Strategy
    reasoning: str
    confidence: float
    alternatives: List[Strategy]
    duration: float = 0.0


class StrategyEngine:
    """Choose execution strategy for tasks.

    Rule-based strategy selection with learning capability.
    """

    def __init__(self, event_bus=None, ai_router=None):
        self.event_bus = event_bus
        self.ai_router = ai_router
        self._strategies = self._initialize_strategies()
        self._strategy_history: List[StrategyResult] = []

    def select(self, task: Dict[str, Any], context: Dict[str, Any] = None) -> StrategyResult:
        """Select best strategy for task.

        Args:
            task: Task description/plan
            context: Additional context

        Returns:
            StrategyResult with selected strategy and reasoning
        """
        start_time = time.perf_counter()
        context = context or {}

        # Get candidate strategies
        candidates = self._match_strategies(task, context)

        # Score strategies
        scored = self._score_strategies(candidates, task, context)

        # Select best
        selected, reasoning = self._select_best(scored, context)

        duration = time.perf_counter() - start_time

        result = StrategyResult(
            selected_strategy=selected,
            reasoning=reasoning,
            confidence=selected.confidence,
            alternatives=[s for s in scored if s.strategy_id != selected.strategy_id],
            duration=duration,
        )

        self._strategy_history.append(result)
        self._emit("STRATEGY_SELECTED", {
            "strategy": selected.strategy_type.value,
            "confidence": selected.confidence,
        })

        return result

    def _initialize_strategies(self) -> List[Strategy]:
        """Initialize built-in strategies."""
        return [
            Strategy(
                strategy_id="fast_1",
                strategy_type=StrategyType.FAST,
                name="Direct Execution",
                description="Execute task directly without planning",
                steps=["Understand request", "Execute directly", "Return result"],
                required_capabilities=["execution"],
                estimated_time=10.0,
                confidence=90.0,
                success_rate=85.0,
            ),
            Strategy(
                strategy_id="deep_1",
                strategy_type=StrategyType.DEEP,
                name="Deep Planning",
                description="Full planning with decomposition and verification",
                steps=["Understand", "Decompose", "Plan", "Execute", "Verify", "Reflect"],
                required_capabilities=["planning", "execution", "verification"],
                estimated_time=120.0,
                confidence=95.0,
                success_rate=92.0,
            ),
            Strategy(
                strategy_id="debug_1",
                strategy_type=StrategyType.DEBUG,
                name="Debug & Fix",
                description="Analyze error, propose fix, verify",
                steps=["Capture error", "Analyze root cause", "Propose fix", "Apply fix", "Test"],
                required_capabilities=["error_analysis", "code_modification", "testing"],
                estimated_time=60.0,
                confidence=85.0,
                success_rate=78.0,
            ),
            Strategy(
                strategy_id="research_1",
                strategy_type=StrategyType.RESEARCH,
                name="Research & Synthesize",
                description="Gather information and synthesize answer",
                steps=["Search sources", "Extract info", "Synthesize", "Validate"],
                required_capabilities=["search", "synthesis"],
                estimated_time=45.0,
                confidence=88.0,
                success_rate=90.0,
            ),
            Strategy(
                strategy_id="creative_1",
                strategy_type=StrategyType.CREATIVE,
                name="Creative Design",
                description="Generate multiple alternatives and select best",
                steps=["Brainstorm", "Evaluate alternatives", "Select best", "Refine"],
                required_capabilities=["generation", "evaluation"],
                estimated_time=180.0,
                confidence=80.0,
                success_rate=75.0,
            ),
            Strategy(
                strategy_id="parallel_1",
                strategy_type=StrategyType.PARALLEL,
                name="Parallel Execution",
                description="Execute independent sub-tasks in parallel",
                steps=["Decompose", "Identify dependencies", "Execute parallel", "Merge results"],
                required_capabilities=["parallel_execution"],
                estimated_time=60.0,
                confidence=85.0,
                success_rate=88.0,
            ),
            Strategy(
                strategy_id="iterative_1",
                strategy_type=StrategyType.ITERATIVE,
                name="Iterative Refinement",
                description="Repeatedly refine until quality threshold met",
                steps=["Initial attempt", "Evaluate", "Refine", "Repeat until quality"],
                required_capabilities=["execution", "evaluation", "refinement"],
                estimated_time=120.0,
                confidence=92.0,
                success_rate=94.0,
            ),
        ]

    def _match_strategies(self, task: Dict[str, Any], context: Dict[str, Any]) -> List[Strategy]:
        """Match strategies to task."""
        task_str = json.dumps(task).lower()
        matched = []

        for strategy in self._strategies:
            score = 0.0
            strategy_desc = strategy.description.lower()

            # Simple keyword matching
            keywords = {
                StrategyType.FAST: ["simple", "quick", "fast", "direct", "status", "help"],
                StrategyType.DEEP: ["complex", "build", "create", "develop", "design", "architecture"],
                StrategyType.DEBUG: ["error", "fix", "debug", "issue", "broken", "failing"],
                StrategyType.RESEARCH: ["search", "find", "research", "what is", "information"],
                StrategyType.CREATIVE: ["design", "creative", "alternative", "innovative"],
                StrategyType.PARALLEL: ["multiple", "batch", "parallel", "concurrent"],
                StrategyType.ITERATIVE: ["quality", "refine", "improve", "optimize"],
            }

            for keyword in keywords.get(strategy.strategy_type, []):
                if keyword in task_str:
                    score += 10.0

            if score > 0:
                strategy.confidence = min(100.0, score + strategy.success_rate * 0.5)
                matched.append(strategy)

        return matched or self._strategies

    def _score_strategies(self, strategies: List[Strategy], task: Dict[str, Any], context: Dict[str, Any]) -> List[Strategy]:
        """Score strategies based on context."""
        for strategy in strategies:
            score = strategy.confidence

            # Boost for historical success
            history = context.get("strategy_history", {}).get(strategy.strategy_type.value, {})
            if history.get("success_rate", 0) > 0.8:
                score += 10.0

            # Penalize for high time
            if strategy.estimated_time > 300:
                score -= 10.0

            strategy.confidence = min(100.0, max(0.0, score))

        return sorted(strategies, key=lambda s: s.confidence, reverse=True)

    def _select_best(self, strategies: List[Strategy], context: Dict[str, Any]) -> tuple[Strategy, str]:
        """Select best strategy."""
        if not strategies:
            return self._strategies[0], "No matching strategies, using default"

        best = strategies[0]
        reasoning = f"Selected {best.name} ({best.strategy_type.value}) with confidence {best.confidence:.0f}%"
        return best, reasoning

    def _emit(self, event_type: str, payload: Dict[str, Any]):
        """Emit event through event bus."""
        if self.event_bus:
            try:
                self.event_bus.publish(event_type, payload)
            except Exception:
                pass

    def get_strategy_stats(self) -> Dict[str, Any]:
        """Get strategy usage statistics."""
        usage: Dict[str, int] = {}
        for result in self._strategy_history:
            strategy_type = result.selected_strategy.strategy_type.value
            usage[strategy_type] = usage.get(strategy_type, 0) + 1

        return {
            "total_decisions": len(self._strategy_history),
            "usage": usage,
            "strategies_available": len(self._strategies),
        }
