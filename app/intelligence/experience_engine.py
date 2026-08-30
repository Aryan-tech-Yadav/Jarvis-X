"""Experience Engine for Jarvis-X.

Records project execution experiences for future learning and reuse.
Each experience captures:
  - project metadata (name, domain, stack, architecture)
  - execution metrics (runtime, coverage, repair count, scores)
  - failures encountered and lessons learned
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class ProjectExperience:
    """Single project execution experience."""

    project_name: str = ""
    domain: str = "general"
    architecture: str = "standard"
    stack: List[str] = field(default_factory=list)
    execution_time_sec: float = 0.0
    planning_score: float = 0.0
    execution_score: float = 0.0
    quality_score: float = 0.0
    test_coverage: float = 0.0
    repair_count: int = 0
    result: str = "SUCCESS"
    failures_encountered: List[Dict[str, Any]] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    modules: List[str] = field(default_factory=list)
    overall_score: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "project_name": self.project_name,
            "domain": self.domain,
            "architecture": self.architecture,
            "stack": list(self.stack),
            "execution_time_sec": self.execution_time_sec,
            "planning_score": self.planning_score,
            "execution_score": self.execution_score,
            "quality_score": self.quality_score,
            "test_coverage": self.test_coverage,
            "repair_count": self.repair_count,
            "result": self.result,
            "failures_encountered": list(self.failures_encountered),
            "lessons_learned": list(self.lessons_learned),
            "modules": list(self.modules),
            "overall_score": self.overall_score,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProjectExperience:
        return cls(
            project_name=str(data.get("project_name", "")),
            domain=str(data.get("domain", "general")),
            architecture=str(data.get("architecture", "standard")),
            stack=list(data.get("stack", [])),
            execution_time_sec=float(data.get("execution_time_sec", 0.0)),
            planning_score=float(data.get("planning_score", 0.0)),
            execution_score=float(data.get("execution_score", 0.0)),
            quality_score=float(data.get("quality_score", 0.0)),
            test_coverage=float(data.get("test_coverage", 0.0)),
            repair_count=int(data.get("repair_count", 0)),
            result=str(data.get("result", "SUCCESS")),
            failures_encountered=list(data.get("failures_encountered", [])),
            lessons_learned=list(data.get("lessons_learned", [])),
            modules=list(data.get("modules", [])),
            overall_score=float(data.get("overall_score", 0.0)),
            created_at=str(data.get("created_at", "")),
            metadata=dict(data.get("metadata", {})),
        )


class ExperienceEngine:
    """Record and retrieve project execution experiences."""

    def __init__(self, experiences_path: str = "data/experiences.json"):
        self.experiences_path = experiences_path
        self._experiences: List[ProjectExperience] = []
        os.makedirs(os.path.dirname(experiences_path) or ".", exist_ok=True)
        self._load()

    def _load(self):
        if not os.path.exists(self.experiences_path):
            return
        try:
            with open(self.experiences_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, list):
                self._experiences = [ProjectExperience.from_dict(item)
                                     for item in raw if isinstance(item, dict)]
        except (OSError, json.JSONDecodeError, TypeError):
            pass

    def _save(self):
        try:
            with open(self.experiences_path, "w", encoding="utf-8") as f:
                json.dump([exp.to_dict() for exp in self._experiences], f, indent=2, default=str)
        except OSError:
            pass

    def record_experience(self, project_name: str, execution_time_sec: float = 0.0,
                          planning_score: float = 0.0, execution_score: float = 0.0,
                          quality_score: float = 0.0, repair_count: int = 0,
                          test_coverage: float = 0.0, result: str = "SUCCESS",
                          domain: str = "general", architecture: str = "standard",
                          stack: Optional[List[str]] = None,
                          failures_encountered: Optional[List[Dict[str, Any]]] = None,
                          lessons_learned: Optional[List[str]] = None,
                          modules: Optional[List[str]] = None,
                          version: str = "v1.0") -> ProjectExperience:
        """Record a new project experience."""
        overall = (planning_score + execution_score + quality_score) / 3.0
        experience = ProjectExperience(
            project_name=project_name,
            domain=domain,
            architecture=architecture,
            stack=list(stack or []),
            execution_time_sec=execution_time_sec,
            planning_score=planning_score,
            execution_score=execution_score,
            quality_score=quality_score,
            test_coverage=test_coverage,
            repair_count=repair_count,
            result=result,
            failures_encountered=list(failures_encountered or []),
            lessons_learned=list(lessons_learned or []),
            modules=list(modules or []),
            overall_score=overall,
            metadata={"version": version},
        )
        self._experiences.append(experience)
        self._save()
        return experience

    def get_experiences(self, domain: Optional[str] = None, limit: Optional[int] = None) -> List[ProjectExperience]:
        """Get recorded experiences, optionally filtered by domain."""
        items = list(self._experiences)
        if domain:
            items = [e for e in items if e.domain == domain]
        if limit is not None:
            items = items[-limit:]
        return items

    def search_similar(self, query: str, limit: int = 5) -> List[ProjectExperience]:
        """Search for similar experiences by goal/domain/architecture."""
        words = set(query.casefold().split())
        scored = []
        for exp in self._experiences:
            haystack = f"{exp.project_name} {exp.domain} {exp.architecture} {' '.join(exp.stack)}".casefold()
            score = sum(word in haystack for word in words)
            if score:
                scored.append((score, exp))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [exp for _, exp in scored[:max(1, limit)]]

    def stats(self) -> Dict[str, Any]:
        """Get aggregate statistics."""
        total = len(self._experiences)
        if total == 0:
            return {"total": 0}
        successes = sum(1 for e in self._experiences if e.result == "SUCCESS")
        return {
            "total": total,
            "successes": successes,
            "failures": total - successes,
            "success_rate": successes / max(1, total),
            "avg_runtime": sum(e.execution_time_sec for e in self._experiences) / total,
            "avg_score": sum(e.overall_score for e in self._experiences) / total,
            "avg_coverage": sum(e.test_coverage for e in self._experiences) / total,
            "total_repairs": sum(e.repair_count for e in self._experiences),
            "domains": list(set(e.domain for e in self._experiences)),
        }

    def all_experiences(self) -> List[ProjectExperience]:
        return list(self._experiences)
