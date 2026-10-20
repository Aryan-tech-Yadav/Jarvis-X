"""Normalize heterogeneous inputs into semantic perception objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Perception:
    source: str
    content: Any
    kind: str = "text"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"source": self.source, "content": self.content, "kind": self.kind,
                "metadata": dict(self.metadata)}


class PerceptionEngine:
    """Convert text, files, logs, and structured project input consistently."""

    def perceive(self, value: Any, source: str = "user", kind: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> Perception:
        if value is None:
            raise ValueError("Perception input cannot be None")
        if isinstance(value, Perception):
            return value
        inferred_kind = kind or (
            "project" if isinstance(value, dict) and "project" in value
            else "text" if isinstance(value, str) else "structured"
        )
        return Perception(source=str(source).strip() or "unknown", content=value,
                          kind=inferred_kind, metadata=dict(metadata or {}))

