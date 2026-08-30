"""Evolution metrics tracking.

Tracks metrics across evolution cycles.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class EvolutionMetrics:
    """Metrics for a single evolution cycle."""

    evolution_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    baseline_score: float = 0.0
    final_score: float = 0.0
    score_improvement: float = 0.0
    improvements_applied: int = 0
    improvements_rejected: int = 0
    duration_seconds: float = 0.0
    llm_calls: int = 0
    tokens_used: int = 0
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    files_modified: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evolution_id": self.evolution_id,
            "timestamp": self.timestamp,
            "baseline_score": round(self.baseline_score, 2),
            "final_score": round(self.final_score, 2),
            "score_improvement": round(self.score_improvement, 2),
            "improvements_applied": self.improvements_applied,
            "improvements_rejected": self.improvements_rejected,
            "duration_seconds": round(self.duration_seconds, 3),
            "llm_calls": self.llm_calls,
            "tokens_used": self.tokens_used,
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "files_modified": list(self.files_modified),
            "metadata": dict(self.metadata),
        }


class EvolutionMetricsTracker:
    """Track and persist evolution metrics."""

    def __init__(self, metrics_file: str = "data/evolution_metrics.json"):
        self.metrics_file = metrics_file
        self.current_metrics: Optional[EvolutionMetrics] = None
        self.history: List[EvolutionMetrics] = []
        self._load()

    def _load(self):
        if os.path.isfile(self.metrics_file):
            try:
                with open(self.metrics_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, list):
                    self.history = [EvolutionMetrics(**item) for item in raw if isinstance(item, dict)]
            except (OSError, json.JSONDecodeError, TypeError):
                pass

    def _save(self):
        os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)
        with open(self.metrics_file, "w", encoding="utf-8") as f:
            json.dump([m.to_dict() for m in self.history], f, indent=2, default=str)

    def start_evolution(self, evolution_id: str, baseline_score: float = 0.0):
        """Start tracking a new evolution."""
        self.current_metrics = EvolutionMetrics(
            evolution_id=evolution_id,
            baseline_score=baseline_score,
        )
        return self.current_metrics

    def record_llm_call(self, tokens: int = 0):
        if self.current_metrics:
            self.current_metrics.llm_calls += 1
            self.current_metrics.tokens_used += tokens

    def record_test(self, passed: bool):
        if self.current_metrics:
            self.current_metrics.tests_run += 1
            if passed:
                self.current_metrics.tests_passed += 1
            else:
                self.current_metrics.tests_failed += 1

    def record_file_modified(self, file_path: str):
        if self.current_metrics and file_path:
            if file_path not in self.current_metrics.files_modified:
                self.current_metrics.files_modified.append(file_path)

    def end_evolution(self, final_score: float, applied: int, rejected: int, duration: float) -> EvolutionMetrics:
        """End tracking and save."""
        if not self.current_metrics:
            self.current_metrics = EvolutionMetrics(evolution_id="unknown")
        
        self.current_metrics.final_score = final_score
        self.current_metrics.score_improvement = final_score - self.current_metrics.baseline_score
        self.current_metrics.improvements_applied = applied
        self.current_metrics.improvements_rejected = rejected
        self.current_metrics.duration_seconds = duration
        
        metrics = self.current_metrics
        self.history.append(metrics)
        self._save()
        self.current_metrics = None
        return metrics

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics."""
        if not self.history:
            return {"total_evolutions": 0}
        
        total = len(self.history)
        avg_improvement = sum(m.score_improvement for m in self.history) / total
        total_applied = sum(m.improvements_applied for m in self.history)
        total_rejected = sum(m.improvements_rejected for m in self.history)
        avg_duration = sum(m.duration_seconds for m in self.history) / total
        
        return {
            "total_evolutions": total,
            "avg_score_improvement": round(avg_improvement, 2),
            "total_improvements_applied": total_applied,
            "total_improvements_rejected": total_rejected,
            "acceptance_rate": round(total_applied / max(1, total_applied + total_rejected), 2),
            "avg_duration": round(avg_duration, 3),
        }
