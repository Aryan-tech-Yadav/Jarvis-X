"""Project experience and execution metrics models for continuous learning."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class StageBreakdown:
    stage_name: str
    score: float
    duration_sec: float
    success: bool
    issues_resolved: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_name": self.stage_name,
            "score": round(float(self.score), 2),
            "duration_sec": round(float(self.duration_sec), 3),
            "success": self.success,
            "issues_resolved": self.issues_resolved,
            "metadata": dict(self.metadata),
        }


@dataclass
class ExecutionMetrics:
    planning_time_sec: float = 0.0
    coding_time_sec: float = 0.0
    test_time_sec: float = 0.0
    repair_time_sec: float = 0.0
    total_time_sec: float = 0.0
    memory_peak_mb: float = 0.0
    cpu_avg_pct: float = 0.0
    tokens_used: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "planning_time_sec": round(float(self.planning_time_sec), 3),
            "coding_time_sec": round(float(self.coding_time_sec), 3),
            "test_time_sec": round(float(self.test_time_sec), 3),
            "repair_time_sec": round(float(self.repair_time_sec), 3),
            "total_time_sec": round(float(self.total_time_sec), 3),
            "memory_peak_mb": round(float(self.memory_peak_mb), 2),
            "cpu_avg_pct": round(float(self.cpu_avg_pct), 2),
            "tokens_used": self.tokens_used,
        }


@dataclass
class ProjectExperience:
    project_id: str = field(default_factory=lambda: str(uuid4()))
    project_name: str = "Unnamed Project"
    domain: str = "general"
    architecture: str = "standard"
    stack: List[str] = field(default_factory=list)
    planning_score: float = 0.0
    execution_score: float = 0.0
    quality_score: float = 0.0
    repair_count: int = 0
    test_coverage: float = 0.0
    result: str = "SUCCESS"  # SUCCESS / FAILED / PARTIAL
    metrics: ExecutionMetrics = field(default_factory=ExecutionMetrics)
    stages: List[StageBreakdown] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "domain": self.domain,
            "architecture": self.architecture,
            "stack": list(self.stack),
            "planning_score": round(float(self.planning_score), 2),
            "execution_score": round(float(self.execution_score), 2),
            "quality_score": round(float(self.quality_score), 2),
            "repair_count": self.repair_count,
            "test_coverage": round(float(self.test_coverage), 2),
            "result": self.result,
            "metrics": self.metrics.to_dict(),
            "stages": [s.to_dict() for s in self.stages],
            "lessons_learned": list(self.lessons_learned),
            "timestamp": self.timestamp,
        }
