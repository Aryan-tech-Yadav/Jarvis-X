"""Engineering Memory for Jarvis-X.

Stores reusable engineering knowledge:
  - Mistakes and how to avoid them
  - Successful fixes
  - Library versions and dependencies
  - Performance tricks
  - Common error patterns
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class EngineeringMemoryEntry:
    """Single engineering memory entry."""

    entry_id: str = ""
    category: str = "general"  # mistake, fix, library, performance, error_pattern
    title: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.entry_id:
            self.entry_id = f"eng-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "tags": list(self.tags),
            "context": dict(self.context),
            "created_at": self.created_at,
        }


class EngineeringMemory:
    """Persistent engineering memory store."""

    def __init__(self, memory_path: str = "data/engineering_memory.json"):
        self.memory_path = memory_path
        self._entries: List[EngineeringMemoryEntry] = []
        os.makedirs(os.path.dirname(memory_path) or ".", exist_ok=True)
        self._load()

    def _load(self):
        if not os.path.exists(self.memory_path):
            return
        try:
            with open(self.memory_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, list):
                self._entries = [EngineeringMemoryEntry(**item) for item in raw if isinstance(item, dict)]
        except (OSError, json.JSONDecodeError, TypeError):
            pass

    def _save(self):
        try:
            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump([e.to_dict() for e in self._entries], f, indent=2, default=str)
        except OSError:
            pass

    def record(self, category: str, title: str, description: str,
               tags: Optional[List[str]] = None, context: Optional[Dict[str, Any]] = None) -> EngineeringMemoryEntry:
        """Record an engineering memory entry."""
        entry = EngineeringMemoryEntry(
            category=category,
            title=title,
            description=description,
            tags=list(tags or []),
            context=dict(context or {}),
        )
        self._entries.append(entry)
        self._save()
        return entry

    def record_mistake(self, mistake: str, fix: str, tags: Optional[List[str]] = None,
                       context: Optional[Dict[str, Any]] = None) -> EngineeringMemoryEntry:
        """Record a mistake and its fix."""
        return self.record(
            category="mistake",
            title=f"Mistake: {mistake[:50]}",
            description=f"Mistake: {mistake}\nFix: {fix}",
            tags=["mistake", "fix"] + (tags or []),
            context=context,
        )

    def record_library(self, library: str, version: str, notes: str = "") -> EngineeringMemoryEntry:
        """Record a library version and usage notes."""
        return self.record(
            category="library",
            title=f"{library} {version}",
            description=notes or f"Using {library} version {version}",
            tags=["library", library.lower()],
            context={"library": library, "version": version},
        )

    def record_performance_trick(self, trick: str, context: Optional[Dict[str, Any]] = None) -> EngineeringMemoryEntry:
        """Record a performance optimization trick."""
        return self.record(
            category="performance",
            title=f"Performance: {trick[:50]}",
            description=trick,
            tags=["performance", "optimization"],
            context=context,
        )

    def search(self, query: str, category: Optional[str] = None, limit: int = 10) -> List[EngineeringMemoryEntry]:
        """Search engineering memory."""
        words = set(query.casefold().split())
        results = []
        for entry in self._entries:
            if category and entry.category != category:
                continue
            haystack = f"{entry.title} {entry.description} {' '.join(entry.tags)}".casefold()
            score = sum(word in haystack for word in words)
            if score:
                results.append((score, entry))
        results.sort(key=lambda pair: pair[0], reverse=True)
        return [entry for _, entry in results[:max(1, limit)]]

    def get_by_category(self, category: str) -> List[EngineeringMemoryEntry]:
        """Get all entries in a category."""
        return [e for e in self._entries if e.category == category]

    def stats(self) -> Dict[str, Any]:
        categories: Dict[str, int] = {}
        for entry in self._entries:
            categories[entry.category] = categories.get(entry.category, 0) + 1
        return {
            "total_entries": len(self._entries),
            "categories": categories,
        }
