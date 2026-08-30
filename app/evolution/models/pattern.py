"""Reusable success patterns, code templates, and architecture blueprints."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class PatternType(str, Enum):
    ARCHITECTURE = "architecture"
    CODE = "code"
    WORKFLOW = "workflow"
    REPAIR = "repair"
    PROMPT = "prompt"


@dataclass
class Pattern:
    pattern_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    pattern_type: PatternType = PatternType.ARCHITECTURE
    domain: str = "general"
    description: str = ""
    blueprint: Dict[str, Any] = field(default_factory=dict)
    benchmark_score: float = 90.0
    times_used: int = 1
    success_rate: float = 1.0
    recommended: bool = True
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "name": self.name,
            "pattern_type": self.pattern_type.value if isinstance(self.pattern_type, PatternType) else str(self.pattern_type),
            "domain": self.domain,
            "description": self.description,
            "blueprint": dict(self.blueprint),
            "benchmark_score": round(float(self.benchmark_score), 2),
            "times_used": self.times_used,
            "success_rate": round(float(self.success_rate), 4),
            "recommended": self.recommended,
            "tags": list(self.tags),
            "created_at": self.created_at,
        }
