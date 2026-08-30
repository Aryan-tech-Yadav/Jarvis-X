"""Knowledge entity and category models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class KnowledgeCategory(str, Enum):
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    PERFORMANCE = "performance"
    REPAIRS = "repairs"
    BENCHMARKS = "benchmarks"
    PATTERNS = "patterns"
    PROMPTS = "prompts"
    LESSONS = "lessons"


@dataclass
class KnowledgeEntry:
    entry_id: str = field(default_factory=lambda: str(uuid4()))
    category: KnowledgeCategory = KnowledgeCategory.LESSONS
    title: str = ""
    summary: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    confidence: float = 0.95
    source_project: str = ""
    version: str = "v1.0"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "category": self.category.value if isinstance(self.category, KnowledgeCategory) else str(self.category),
            "title": self.title,
            "summary": self.summary,
            "content": dict(self.content),
            "tags": list(self.tags),
            "confidence": round(float(self.confidence), 4),
            "source_project": self.source_project,
            "version": self.version,
            "created_at": self.created_at,
        }
