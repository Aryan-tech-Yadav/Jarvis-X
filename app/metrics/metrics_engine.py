"""Enhanced metrics engine for engineering pipeline execution.

Tracks execution time, LLM calls, tokens, retries, repair count,
success rate, and other engineering metrics.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ExecutionMetrics:
    """Metrics for a single pipeline execution."""

    goal: str = ""
    project_name: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    success: bool = False
    agents_used: List[str] = field(default_factory=list)
    llm_calls: int = 0
    prompt_tokens: int = 0
    response_tokens: int = 0
    retries: int = 0
    repair_count: int = 0
    files_generated: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "project_name": self.project_name,
            "duration": round(self.duration, 3),
            "success": self.success,
            "agents_used": list(self.agents_used),
            "llm_calls": self.llm_calls,
            "prompt_tokens": self.prompt_tokens,
            "response_tokens": self.response_tokens,
            "retries": self.retries,
            "repair_count": self.repair_count,
            "files_generated": self.files_generated,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


class MetricsEngine:
    """Collect, aggregate, and persist engineering metrics."""

    def __init__(self, metrics_file: str = os.path.join("data", "metrics.json")):
        self.metrics_file = metrics_file
        self.current_metrics: Optional[ExecutionMetrics] = None
        self.history: List[ExecutionMetrics] = []
        self._load()

    def _load(self):
        if os.path.isfile(self.metrics_file):
            try:
                with open(self.metrics_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, list):
                    self.history = [ExecutionMetrics(**item) for item in raw if isinstance(item, dict)]
            except (OSError, json.JSONDecodeError, TypeError):
                pass

    def _save(self):
        os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)
        with open(self.metrics_file, "w", encoding="utf-8") as f:
            json.dump([m.to_dict() for m in self.history], f, indent=2)

    def start_execution(self, goal: str, project_name: str = "") -> ExecutionMetrics:
        """Start tracking a new execution."""
        self.current_metrics = ExecutionMetrics(
            goal=goal,
            project_name=project_name,
            start_time=time.perf_counter(),
        )
        return self.current_metrics

    def record_agent(self, agent_name: str):
        if self.current_metrics:
            self.current_metrics.agents_used.append(agent_name)

    def record_llm_call(self, prompt_tokens: int = 0, response_tokens: int = 0):
        if self.current_metrics:
            self.current_metrics.llm_calls += 1
            self.current_metrics.prompt_tokens += prompt_tokens
            self.current_metrics.response_tokens += response_tokens

    def record_retry(self):
        if self.current_metrics:
            self.current_metrics.retries += 1

    def record_repair(self):
        if self.current_metrics:
            self.current_metrics.repair_count += 1

    def record_files(self, count: int):
        if self.current_metrics:
            self.current_metrics.files_generated += count

    def add_error(self, error: str):
        if self.current_metrics:
            self.current_metrics.errors.append(error)

    def add_warning(self, warning: str):
        if self.current_metrics:
            self.current_metrics.warnings.append(warning)

    def end_execution(self, success: bool) -> ExecutionMetrics:
        """End tracking and save to history."""
        if not self.current_metrics:
            self.current_metrics = ExecutionMetrics()
        
        self.current_metrics.end_time = time.perf_counter()
        self.current_metrics.duration = self.current_metrics.end_time - self.current_metrics.start_time
        self.current_metrics.success = success
        
        metrics = self.current_metrics
        self.history.append(metrics)
        self._save()
        self.current_metrics = None
        return metrics

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics from history."""
        if not self.history:
            return {"total_executions": 0}
        
        total = len(self.history)
        successful = sum(1 for m in self.history if m.success)
        avg_duration = sum(m.duration for m in self.history) / total
        total_llm_calls = sum(m.llm_calls for m in self.history)
        total_files = sum(m.files_generated for m in self.history)
        total_errors = sum(len(m.errors) for m in self.history)
        
        return {
            "total_executions": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": round(successful / total, 2) if total else 0.0,
            "avg_duration": round(avg_duration, 3),
            "total_llm_calls": total_llm_calls,
            "total_files_generated": total_files,
            "total_errors": total_errors,
        }

    def get_current(self) -> Optional[ExecutionMetrics]:
        return self.current_metrics
