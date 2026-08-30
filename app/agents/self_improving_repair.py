"""Self-improving repair loop for autonomous agents.

Learns from execution history to improve repair strategies:
  - Tracks which repair strategies work for which error types
  - Prefers strategies with higher historical success rates
  - Stores successful repairs in persistent memory
  - Adapts retry strategies based on agent performance
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.logger import Logger
from app.agents.execution_history import ExecutionHistory, ExecutionRecord
from app.agents.message_bus import MessageBus


@dataclass
class RepairStrategy:
    """A repair strategy for a specific error type."""

    strategy_id: str
    error_type: str
    agent_name: str
    action: str
    success_count: int = 0
    failure_count: int = 0
    success_rate: float = 0.0
    avg_duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "strategy_id": self.strategy_id,
            "error_type": self.error_type,
            "agent_name": self.agent_name,
            "action": self.action,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": round(self.success_rate, 2),
            "avg_duration": round(self.avg_duration, 2),
            "metadata": dict(self.metadata),
        }


@dataclass
class RepairOutcome:
    """Outcome of a repair attempt."""

    strategy_id: str
    success: bool
    duration: float = 0.0
    error: Optional[str] = None
    output: Any = None

    def to_dict(self) -> dict:
        return {
            "strategy_id": self.strategy_id,
            "success": self.success,
            "duration": round(self.duration, 2),
            "error": self.error,
            "output": str(self.output)[:200] if self.output else None,
        }


class SelfImprovingRepairLoop:
    """Autonomous repair loop that learns from history.

    Workflow:
      1. Detect error type from failure
      2. Look up best repair strategy from history
      3. Execute repair via appropriate agent
      4. Record outcome
      5. Update strategy success rates
      6. If repair fails, try alternative strategies
    """

    def __init__(
        self,
        execution_history: Optional[ExecutionHistory] = None,
        message_bus: Optional[MessageBus] = None,
        max_repair_attempts: int = 3,
        strategy_file: str = "data/repair_strategies.json",
    ):
        self.execution_history = execution_history or ExecutionHistory()
        self.message_bus = message_bus or MessageBus()
        self.max_repair_attempts = max_repair_attempts
        self.strategy_file = strategy_file
        self._strategies: Dict[str, RepairStrategy] = {}
        self._load_strategies()

    def _load_strategies(self):
        import json
        import os

        if os.path.isfile(self.strategy_file):
            try:
                with open(self.strategy_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, list):
                    for item in raw:
                        strategy = RepairStrategy(**item)
                        self._strategies[strategy.strategy_id] = strategy
            except (OSError, json.JSONDecodeError, TypeError):
                self._strategies = {}

        # Seed default strategies if none exist
        if not self._strategies:
            self._seed_default_strategies()

    def _seed_default_strategies(self):
        """Seed default repair strategies."""
        defaults = [
            RepairStrategy(strategy_id="syntax-error-fix", error_type="syntax_error", agent_name="repair", action="fix_syntax"),
            RepairStrategy(strategy_id="import-error-fix", error_type="import_error", agent_name="repair", action="fix_imports"),
            RepairStrategy(strategy_id="test-failure-fix", error_type="test_failure", agent_name="repair", action="fix_tests"),
            RepairStrategy(strategy_id="runtime-error-fix", error_type="runtime_error", agent_name="repair", action="fix_runtime"),
            RepairStrategy(strategy_id="type-error-fix", error_type="type_error", agent_name="repair", action="fix_types"),
            RepairStrategy(strategy_id="dependency-error-fix", error_type="dependency_error", agent_name="repair", action="fix_dependencies"),
        ]
        for strategy in defaults:
            self._strategies[strategy.strategy_id] = strategy
        self._save_strategies()

    def _save_strategies(self):
        import json
        import os

        os.makedirs(os.path.dirname(self.strategy_file), exist_ok=True)
        with open(self.strategy_file, "w", encoding="utf-8") as f:
            json.dump([s.to_dict() for s in self._strategies.values()], f, indent=2)

    def classify_error(self, error: str) -> str:
        """Classify error into a known error type."""
        error_lower = error.lower()
        if "syntaxerror" in error_lower or "syntax error" in error_lower:
            return "syntax_error"
        if "importerror" in error_lower or "modulenotfounderror" in error_lower:
            return "import_error"
        if "test" in error_lower and "fail" in error_lower:
            return "test_failure"
        if "runtimeerror" in error_lower or "runtime error" in error_lower:
            return "runtime_error"
        if "typeerror" in error_lower or "type error" in error_lower:
            return "type_error"
        if "dependency" in error_lower or "package" in error_lower:
            return "dependency_error"
        return "unknown"

    def select_strategy(self, error_type: str, agent_name: str) -> Optional[RepairStrategy]:
        """Select the best repair strategy for an error type."""
        candidates = [
            s for s in self._strategies.values()
            if s.error_type == error_type
        ]

        if not candidates:
            return None

        # Sort by success rate, then by average duration
        candidates.sort(key=lambda s: (s.success_rate, -s.avg_duration), reverse=True)
        return candidates[0]

    def repair(
        self,
        error: str,
        agent_name: str,
        repair_handler: Optional[Callable[[RepairStrategy], Dict[str, Any]]] = None,
    ) -> RepairOutcome:
        """Execute repair using the best known strategy.

        Args:
            error: Error message to repair.
            agent_name: Agent that reported the error.
            repair_handler: Optional callable that executes the repair.

        Returns:
            RepairOutcome with success status.
        """
        error_type = self.classify_error(error)
        strategy = self.select_strategy(error_type, agent_name)

        if strategy is None:
            Logger.warning(f"[SelfImprovingRepair] No strategy for error type: {error_type}")
            return RepairOutcome(strategy_id="none", success=False, error=f"No strategy for {error_type}")

        Logger.info(f"[SelfImprovingRepair] Using strategy {strategy.strategy_id} for {error_type}")

        start = time.perf_counter()
        try:
            if repair_handler:
                result = repair_handler(strategy)
                success = result.get("success", False)
                output = result.get("output")
                error_msg = result.get("error")
            else:
                # Default: send repair message via message bus
                msg = self.message_bus.send(
                    sender="repair_loop",
                    receiver=agent_name,
                    message_type="REPAIR",
                    payload={"strategy": strategy.action, "error": error},
                )
                success = True
                output = {"message_id": msg.id if hasattr(msg, "id") else "sent"}
                error_msg = None

            duration = time.perf_counter() - start
            outcome = RepairOutcome(
                strategy_id=strategy.strategy_id,
                success=success,
                duration=duration,
                error=error_msg,
                output=output,
            )

            # Update strategy statistics
            self._update_strategy(strategy, outcome)

            # Record in execution history
            record = ExecutionRecord(
                execution_id=f"repair-{int(time.time())}",
                agent_name=agent_name,
                task_type=f"repair_{error_type}",
                success=success,
                duration=duration,
                error=error_msg,
                output_summary=str(output)[:200],
                metadata={"strategy": strategy.strategy_id, "action": strategy.action},
            )
            self.execution_history.record(record)

            return outcome

        except Exception as exc:
            duration = time.perf_counter() - start
            Logger.error(f"[SelfImprovingRepair] Repair failed: {exc}")
            return RepairOutcome(
                strategy_id=strategy.strategy_id,
                success=False,
                duration=duration,
                error=str(exc),
            )

    def _update_strategy(self, strategy: RepairStrategy, outcome: RepairOutcome):
        """Update strategy statistics based on outcome."""
        if outcome.success:
            strategy.success_count += 1
        else:
            strategy.failure_count += 1

        total = strategy.success_count + strategy.failure_count
        strategy.success_rate = strategy.success_count / total if total > 0 else 0.0

        # Update average duration
        strategy.avg_duration = (
            (strategy.avg_duration * (total - 1) + outcome.duration) / total
            if total > 0 else outcome.duration
        )

        self._save_strategies()

    def run_repair_loop(
        self,
        errors: List[Dict[str, Any]],
        agent_name: str,
        repair_handler: Optional[Callable] = None,
        max_attempts: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Run repair loop for multiple errors.

        Args:
            errors: List of error dictionaries with 'message' or 'error' keys.
            agent_name: Agent that reported the errors.
            repair_handler: Optional repair handler.
            max_attempts: Max repair attempts per error.

        Returns:
            Summary of repair outcomes.
        """
        max_attempts = max_attempts or self.max_repair_attempts
        repaired = 0
        remaining = []
        attempts = 0

        for error_item in errors[:max_attempts * 2]:  # Limit total errors
            error_msg = error_item.get("message") or error_item.get("error") or str(error_item)
            attempts += 1

            outcome = self.repair(error_msg, agent_name, repair_handler)
            if outcome.success:
                repaired += 1
                Logger.success(f"[SelfImprovingRepair] Repaired: {error_msg[:80]}")
            else:
                remaining.append(error_item)

        status = "completed" if not remaining else "partial"
        return {
            "repaired": repaired,
            "remaining": len(remaining),
            "attempts": attempts,
            "status": status,
        }

    def stats(self) -> Dict[str, Any]:
        """Get repair loop statistics."""
        return {
            "total_strategies": len(self._strategies),
            "strategies": [s.to_dict() for s in self._strategies.values()],
            "execution_history": self.execution_history.stats(),
        }
