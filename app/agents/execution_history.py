"""Agent execution history and performance tracking.

Records every agent execution, builds performance profiles,
and exposes statistics to help the orchestrator make better decisions.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ExecutionRecord:
    """Single agent execution record."""

    execution_id: str
    agent_name: str
    task_type: str
    success: bool
    duration: float = 0.0
    error: Optional[str] = None
    output_summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "agent_name": self.agent_name,
            "task_type": self.task_type,
            "success": self.success,
            "duration": round(self.duration, 2),
            "error": self.error,
            "output_summary": self.output_summary[:200],
            "metadata": dict(self.metadata),
            "timestamp": round(self.timestamp, 2),
        }


@dataclass
class AgentPerformanceProfile:
    """Aggregated performance profile for an agent."""

    agent_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_duration: float = 0.0
    avg_duration: float = 0.0
    success_rate: float = 0.0
    common_errors: List[str] = field(default_factory=list)
    task_success_rates: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "total_duration": round(self.total_duration, 2),
            "avg_duration": round(self.avg_duration, 2),
            "success_rate": round(self.success_rate, 2),
            "common_errors": list(self.common_errors[:5]),
            "task_success_rates": {k: round(v, 2) for k, v in self.task_success_rates.items()},
        }


class ExecutionHistory:
    """Persist and query agent execution history.

    Stores records on disk so learning survives restarts.
    """

    def __init__(self, history_file: str = "data/agent_execution_history.json"):
        self.history_file = history_file
        self._records: List[ExecutionRecord] = []
        self._profiles: Dict[str, AgentPerformanceProfile] = {}
        self._load()

    def _load(self):
        if os.path.isfile(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, list):
                    self._records = [ExecutionRecord(**item) for item in raw if isinstance(item, dict)]
                    self._rebuild_profiles()
            except (OSError, json.JSONDecodeError, TypeError):
                self._records = []

    def _save(self):
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in self._records], f, indent=2)

    def _rebuild_profiles(self):
        self._profiles = {}
        for record in self._records:
            profile = self._profiles.setdefault(record.agent_name, AgentPerformanceProfile(agent_name=record.agent_name))
            profile.total_executions += 1
            if record.success:
                profile.successful_executions += 1
            else:
                profile.failed_executions += 1
                if record.error and record.error not in profile.common_errors:
                    profile.common_errors.append(record.error)
            profile.total_duration += record.duration
            profile.avg_duration = profile.total_duration / profile.total_executions
            profile.success_rate = profile.successful_executions / profile.total_executions

            # Track task-type success rates
            if record.task_type not in profile.task_success_rates:
                profile.task_success_rates[record.task_type] = 1.0 if record.success else 0.0
            else:
                current = profile.task_success_rates[record.task_type]
                count = sum(1 for r in self._records if r.agent_name == record.agent_name and r.task_type == record.task_type)
                profile.task_success_rates[record.task_type] = (
                    (current * (count - 1) + (1.0 if record.success else 0.0)) / count
                )

    def record(self, record: ExecutionRecord):
        """Record a new execution."""
        self._records.append(record)
        self._save()
        self._update_profile(record)

    def _update_profile(self, record: ExecutionRecord):
        profile = self._profiles.setdefault(record.agent_name, AgentPerformanceProfile(agent_name=record.agent_name))
        profile.total_executions += 1
        if record.success:
            profile.successful_executions += 1
        else:
            profile.failed_executions += 1
            if record.error and record.error not in profile.common_errors:
                profile.common_errors.append(record.error)
        profile.total_duration += record.duration
        profile.avg_duration = profile.total_duration / profile.total_executions
        profile.success_rate = profile.successful_executions / profile.total_executions

        if record.task_type not in profile.task_success_rates:
            profile.task_success_rates[record.task_type] = 1.0 if record.success else 0.0

    def get_profile(self, agent_name: str) -> Optional[AgentPerformanceProfile]:
        """Get performance profile for an agent."""
        return self._profiles.get(agent_name)

    def get_records(self, agent_name: Optional[str] = None, task_type: Optional[str] = None, limit: int = 100) -> List[ExecutionRecord]:
        """Get execution records with optional filters."""
        records = self._records
        if agent_name:
            records = [r for r in records if r.agent_name == agent_name]
        if task_type:
            records = [r for r in records if r.task_type == task_type]
        return records[-limit:]

    def get_best_agent(self, task_type: str, candidates: List[str]) -> Optional[str]:
        """Select the best agent for a task type based on history."""
        best_agent = None
        best_score = -1.0

        for agent_name in candidates:
            profile = self._profiles.get(agent_name)
            if not profile:
                continue
            task_success = profile.task_success_rates.get(task_type, profile.success_rate)
            score = task_success * 0.7 + (1.0 - min(profile.avg_duration, 10.0) / 10.0) * 0.3
            if score > best_score:
                best_score = score
                best_agent = agent_name

        return best_agent

    def stats(self) -> Dict[str, Any]:
        """Get global execution statistics."""
        total = len(self._records)
        successful = sum(1 for r in self._records if r.success)
        return {
            "total_executions": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": round(successful / total, 2) if total else 0.0,
            "tracked_agents": len(self._profiles),
        }
