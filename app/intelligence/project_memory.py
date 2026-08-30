"""Project Memory for Jarvis-X.

Stores structured memory of past projects including:
  - folder structures
  - architecture decisions
  - best practices
  - problems encountered
  - solutions applied
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class ProjectMemory:
    """Memory entry for a single project."""

    project_name: str = ""
    version: str = "v1"
    folder_structure: Dict[str, Any] = field(default_factory=dict)
    architecture: Dict[str, Any] = field(default_factory=dict)
    best_practices: List[str] = field(default_factory=list)
    problems: List[Dict[str, Any]] = field(default_factory=list)
    solutions: List[Dict[str, Any]] = field(default_factory=list)
    stack: List[str] = field(default_factory=list)
    domain: str = "general"
    overall_score: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "project_name": self.project_name,
            "version": self.version,
            "folder_structure": dict(self.folder_structure),
            "architecture": dict(self.architecture),
            "best_practices": list(self.best_practices),
            "problems": list(self.problems),
            "solutions": list(self.solutions),
            "stack": list(self.stack),
            "domain": self.domain,
            "overall_score": self.overall_score,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProjectMemory:
        return cls(
            project_name=str(data.get("project_name", "")),
            version=str(data.get("version", "v1")),
            folder_structure=dict(data.get("folder_structure", {})),
            architecture=dict(data.get("architecture", {})),
            best_practices=list(data.get("best_practices", [])),
            problems=list(data.get("problems", [])),
            solutions=list(data.get("solutions", [])),
            stack=list(data.get("stack", [])),
            domain=str(data.get("domain", "general")),
            overall_score=float(data.get("overall_score", 0.0)),
            created_at=str(data.get("created_at", "")),
            updated_at=str(data.get("updated_at", "")),
            metadata=dict(data.get("metadata", {})),
        )


class ProjectMemoryStore:
    """Persistent storage for project memories."""

    def __init__(self, memory_path: str = "data/project_memory.json"):
        self.memory_path = memory_path
        self._memories: Dict[str, ProjectMemory] = {}
        os.makedirs(os.path.dirname(memory_path) or ".", exist_ok=True)
        self._load()

    def _load(self):
        if not os.path.exists(self.memory_path):
            return
        try:
            with open(self.memory_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                for key, data in raw.items():
                    self._memories[key] = ProjectMemory.from_dict(data)
        except (OSError, json.JSONDecodeError, TypeError):
            pass

    def _save(self):
        try:
            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump({k: v.to_dict() for k, v in self._memories.items()}, f, indent=2, default=str)
        except OSError:
            pass

    def store(self, memory: ProjectMemory) -> str:
        """Store a project memory."""
        key = f"{memory.project_name}:{memory.version}"
        memory.updated_at = datetime.now(timezone.utc).isoformat()
        self._memories[key] = memory
        self._save()
        return key

    def get(self, project_name: str, version: str = "v1") -> Optional[ProjectMemory]:
        """Get a specific project memory."""
        key = f"{project_name}:{version}"
        return self._memories.get(key)

    def find_similar(self, project_name: str, domain: Optional[str] = None, limit: int = 5) -> List[ProjectMemory]:
        """Find similar project memories."""
        candidates = list(self._memories.values())
        if domain:
            candidates = [m for m in candidates if m.domain == domain]
        # Simple similarity: match project name or domain keywords
        words = set(project_name.casefold().split())
        scored = []
        for mem in candidates:
            haystack = f"{mem.project_name} {mem.domain} {' '.join(mem.stack)}".casefold()
            score = sum(word in haystack for word in words)
            if score:
                scored.append((score, mem))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [mem for _, mem in scored[:max(1, limit)]]

    def add_solution(self, project_name: str, problem: str, solution: str, version: str = "v1"):
        """Add a problem-solution pair to project memory."""
        memory = self.get(project_name, version)
        if memory is None:
            memory = ProjectMemory(project_name=project_name, version=version)
        memory.problems.append({"problem": problem, "timestamp": datetime.now(timezone.utc).isoformat()})
        memory.solutions.append({"solution": solution, "problem": problem, "timestamp": datetime.now(timezone.utc).isoformat()})
        memory.updated_at = datetime.now(timezone.utc).isoformat()
        self.store(memory)

    def stats(self) -> Dict[str, Any]:
        return {
            "total_projects": len(self._memories),
            "domains": list(set(m.domain for m in self._memories.values())),
            "avg_score": sum(m.overall_score for m in self._memories.values()) / max(1, len(self._memories)),
        }
