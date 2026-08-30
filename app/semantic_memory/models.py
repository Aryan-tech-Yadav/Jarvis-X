from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Tuple
from uuid import uuid4

from app.semantic_memory.validators import (
    normalized_metadata,
    normalized_score,
    normalized_tags,
    normalized_text,
)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class SemanticMemory:
    """A durable recollection with explicit provenance and ranking signals."""

    content: str
    memory_type: str = "experience"
    tags: Tuple[str, ...] = field(default_factory=tuple)
    importance: float = 0.5
    confidence: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)
    memory_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def __post_init__(self):
        object.__setattr__(self, "content", normalized_text(self.content))
        object.__setattr__(self, "memory_type", normalized_text(self.memory_type, "memory_type").casefold())
        object.__setattr__(self, "tags", normalized_tags(self.tags))
        object.__setattr__(self, "importance", normalized_score(self.importance, "importance"))
        object.__setattr__(self, "confidence", normalized_score(self.confidence, "confidence"))
        object.__setattr__(self, "metadata", normalized_metadata(self.metadata))
        object.__setattr__(self, "memory_id", normalized_text(self.memory_id, "memory_id"))

    def to_dict(self):
        return {
            "id": self.memory_id,
            "content": self.content,
            "memory_type": self.memory_type,
            "tags": list(self.tags),
            "importance": self.importance,
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, value):
        if not isinstance(value, dict):
            raise ValueError("semantic memory must be a dictionary")
        return cls(
            content=value.get("content"),
            memory_type=value.get("memory_type", "experience"),
            tags=value.get("tags", ()),
            importance=value.get("importance", 0.5),
            confidence=value.get("confidence", 0.5),
            metadata=value.get("metadata", {}),
            memory_id=value.get("id") or value.get("memory_id") or str(uuid4()),
            created_at=value.get("created_at") or utc_now(),
            updated_at=value.get("updated_at") or utc_now(),
        )
