"""Engineering memory persistence.

Stores per-project engineering memories so future projects can reuse
learnings, prompts, fixes, and benchmark results.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProjectMemory:
    """Memory record for a single completed project."""

    project_name: str
    goal: str = ""
    architecture: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    fixes: List[Dict[str, Any]] = field(default_factory=list)
    runtime_notes: List[str] = field(default_factory=list)
    llm_prompts: List[Dict[str, Any]] = field(default_factory=list)
    benchmark: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    success_rate: float = 0.0
    duration_seconds: float = 0.0
    tokens_used: int = 0
    artifacts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "goal": self.goal,
            "architecture": dict(self.architecture),
            "errors": list(self.errors),
            "fixes": list(self.fixes),
            "runtime_notes": list(self.runtime_notes),
            "llm_prompts": list(self.llm_prompts),
            "benchmark": dict(self.benchmark),
            "success": self.success,
            "success_rate": round(self.success_rate, 2),
            "duration_seconds": round(self.duration_seconds, 3),
            "tokens_used": self.tokens_used,
            "artifacts": list(self.artifacts),
        }


class EngineeringMemory:
    """Persist and retrieve engineering memories across projects."""

    def __init__(self, memory_file: str = os.path.join("data", "engineering_memory.json")):
        self.memory_file = memory_file
        self._memories: List[ProjectMemory] = []
        self._load()

    def _load(self):
        if os.path.isfile(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, list):
                    self._memories = [ProjectMemory(**item) for item in raw if isinstance(item, dict)]
            except (OSError, json.JSONDecodeError, TypeError):
                self._memories = []

    def _save(self):
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump([m.to_dict() for m in self._memories], f, indent=2)

    def add_memory(self, memory: ProjectMemory):
        self._memories.append(memory)
        self._save()

    def get_memory(self, project_name: str) -> Optional[ProjectMemory]:
        for memory in reversed(self._memories):
            if memory.project_name == project_name:
                return memory
        return None

    def search_similar(self, goal: str, limit: int = 5) -> List[ProjectMemory]:
        """Return memories whose goal text is most similar to the provided goal."""
        scored = []
        goal_lower = goal.lower()
        for memory in self._memories:
            score = self._similarity(goal_lower, memory.goal.lower())
            scored.append((score, memory))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [memory for _, memory in scored[:limit]]

    def all_memories(self) -> List[ProjectMemory]:
        return list(self._memories)

    def stats(self) -> Dict[str, Any]:
        total = len(self._memories)
        success_count = sum(1 for m in self._memories if m.success)
        return {
            "total_projects": total,
            "successful": success_count,
            "failed": total - success_count,
            "success_rate": round(success_count / total, 2) if total else 0.0,
        }

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        a_words = set(a.split())
        b_words = set(b.split())
        intersection = a_words & b_words
        union = a_words | b_words
        return len(intersection) / len(union) if union else 0.0
