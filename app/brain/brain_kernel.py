"""Brain Kernel - Main orchestrator for Engineering Intelligence Kernel (EIK).

Ties together all brain modules:
  - Thinking Engine
  - Decision Engine
  - Error Intelligence
  - Strategy Engine
  - Reflection Engine
  - Evolution Engine
  - Brain Analytics

This is the "brain kernel" that makes Jarvis intelligent.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.logger import Logger
from app.brain.thinking.thinking_engine import ThinkingEngine, ThinkingMode, ThinkingResult
from app.brain.decision.decision_engine import DecisionEngine, DecisionResult
from app.brain.strategy.strategy_engine import StrategyEngine, StrategyResult
from app.brain.error_intelligence.error_intelligence import ErrorIntelligence, ErrorAnalysis
from app.brain.reflection.reflection_engine import ReflectionEngine, ReflectionReport
from app.brain.evolution.evolution_engine import EvolutionEngine
from app.brain.analytics.brain_analytics import BrainAnalytics


@dataclass
class BrainContext:
    """Context for brain processing."""
    session_id: str = ""
    user_input: str = ""
    thinking_result: Optional[ThinkingResult] = None
    decision_result: Optional[DecisionResult] = None
    strategy_result: Optional[StrategyResult] = None
    error_analysis: Optional[ErrorAnalysis] = None
    reflection_report: Optional[ReflectionReport] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BrainKernel:
    """Main brain kernel orchestrator.

    Pipeline for every task:
      1. Think (understand, decompose, plan)
      2. Decide (score plans, select best)
      3. Choose Strategy
      4. Execute (delegated to executor)
      5. Reflect (analyze outcome)
      6. Learn (update rules/memory)
      7. Evolve (periodic improvement)

    This is the "brain" of Jarvis - never gives direct answers,
    always thinks first.
    """

    def __init__(self, event_bus=None, ai_router=None, runtime_context=None):
        self.event_bus = event_bus
        self.ai_router = ai_router
        self.runtime_context = runtime_context

        # Initialize all brain modules
        self.thinking = ThinkingEngine(ai_router=ai_router, event_bus=event_bus)
        self.decision = DecisionEngine(event_bus=event_bus)
        self.strategy = StrategyEngine(event_bus=event_bus, ai_router=ai_router)
        self.error_intelligence = ErrorIntelligence(event_bus=event_bus, ai_router=ai_router)
        self.reflection = ReflectionEngine(event_bus=event_bus)
        self.evolution = EvolutionEngine(event_bus=event_bus, ai_router=ai_router)
        self.analytics = BrainAnalytics()

        self._context = BrainContext()
        self._processing_count = 0

        Logger.success("[BrainKernel] Engineering Intelligence Kernel initialized")

    def process(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process user input through brain kernel.

        Args:
            user_input: User's request
            context: Additional context

        Returns:
            Processing result with plan, strategy, and reasoning
        """
        self._processing_count += 1
        context = context or {}
        start_time = time.perf_counter()

        self._context = BrainContext(
            session_id=context.get("session_id", f"session_{self._processing_count}"),
            user_input=user_input,
        )

        Logger.info(f"[BrainKernel] Processing: {user_input[:50]}...")

        # Step 1: Think
        thinking_result = self.thinking.think(user_input, context)
        self._context.thinking_result = thinking_result

        # Step 2: Decide
        if thinking_result.plans:
            decision_result = self.decision.decide(thinking_result.plans, context)
            self._context.decision_result = decision_result
        else:
            decision_result = None

        # Step 3: Choose Strategy
        task_for_strategy = {
            "problem": user_input,
            "plan": {
                "plan_id": thinking_result.selected_plan.plan_id if thinking_result.selected_plan else "",
                "description": thinking_result.selected_plan.description if thinking_result.selected_plan else "",
                "steps": thinking_result.selected_plan.steps if thinking_result.selected_plan else [],
            },
            "complexity": "high" if thinking_result.thinking_mode == ThinkingMode.DEEP else "low",
        }
        strategy_result = self.strategy.select(task_for_strategy, context)
        self._context.strategy_result = strategy_result

        duration = time.perf_counter() - start_time

        result = {
            "thinking": {
                "mode": thinking_result.thinking_mode.value,
                "understanding": thinking_result.understanding,
                "sub_problems": [
                    {"id": sp.sub_problem_id, "description": sp.description}
                    for sp in thinking_result.sub_problems
                ],
                "plans_generated": len(thinking_result.plans),
                "confidence": thinking_result.confidence,
            },
            "decision": {
                "selected_plan": decision_result.selected_plan_id if decision_result else None,
                "reasoning": decision_result.reasoning if decision_result else "",
                "confidence": decision_result.confidence if decision_result else 0.0,
                "all_scores": [
                    {"plan": s.plan_id, "score": s.overall}
                    for s in (decision_result.all_scores if decision_result else [])
                ],
            },
            "strategy": {
                "selected": strategy_result.selected_strategy.strategy_type.value,
                "name": strategy_result.selected_strategy.name,
                "reasoning": strategy_result.reasoning,
                "confidence": strategy_result.confidence,
            },
            "duration": duration,
            "processing_count": self._processing_count,
        }

        # Record for analytics
        self.analytics.record_task({
            "task_id": self._context.session_id,
            "success": True,
            "confidence": thinking_result.confidence,
            "quality_score": thinking_result.confidence,
            "strategy": strategy_result.selected_strategy.strategy_type.value,
            "timestamp": datetime.now().isoformat(),
        })

        # Record for evolution
        self.evolution.record_task({
            "task_id": self._context.session_id,
            "success": True,
            "quality_score": thinking_result.confidence,
            "metrics": {"duration_seconds": duration},
        })

        self._emit("BRAIN_PROCESSING_COMPLETED", result)
        return result

    def reflect_on_task(self, task_result: Dict[str, Any]) -> ReflectionReport:
        """Reflect on completed task.

        Args:
            task_result: Task execution result

        Returns:
            ReflectionReport with insights
        """
        report = self.reflection.reflect(task_result, {
            "thinking": self._context.thinking_result,
            "decision": self._context.decision_result,
            "strategy": self._context.strategy_result,
        })

        self._context.reflection_report = report

        # Learn from reflection
        if report.should_update_memory:
            Logger.info("[BrainKernel] Updating memory based on reflection")

        if report.should_update_rules:
            Logger.info("[BrainKernel] Updating rules based on reflection")

        return report

    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle error through error intelligence.

        Args:
            error: Exception object
            context: Error context

        Returns:
            Error analysis and proposed fix
        """
        analysis = self.error_intelligence.analyze(error, context)
        fix = self.error_intelligence.propose_fix(analysis)

        return {
            "analysis": {
                "category": analysis.category.value,
                "root_cause": analysis.root_cause,
                "severity": analysis.severity,
            },
            "fix": fix,
        }

    def get_analytics_report(self) -> str:
        """Get analytics report."""
        return self.analytics.get_report_summary()

    def get_brain_stats(self) -> Dict[str, Any]:
        """Get brain statistics."""
        analytics_report = self.analytics.get_latest_report()
        return {
            "tasks_processed": self._processing_count,
            "thinking_history": len(self.thinking.get_history()),
            "decision_history": len(self.decision.get_decision_history()),
            "strategy_stats": self.strategy.get_strategy_stats(),
            "reflection_stats": self.reflection.get_reflection_stats(),
            "evolution_stats": self.evolution.get_evolution_stats(),
            "error_stats": self.error_intelligence.get_error_stats(),
            "analytics": {
                "date": analytics_report.date if analytics_report else "",
                "total_tasks": analytics_report.total_tasks if analytics_report else 0,
                "planning_accuracy": analytics_report.planning_accuracy if analytics_report else 0.0,
                "weakest_skill": analytics_report.weakest_skill if analytics_report else "",
            } if analytics_report else {},
        }

    def _emit(self, event_type: str, payload: Dict[str, Any]):
        """Emit event through event bus."""
        if self.event_bus:
            try:
                self.event_bus.publish(event_type, payload)
            except Exception:
                pass
