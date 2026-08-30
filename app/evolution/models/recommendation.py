"""Proactive recommendation and optimization impact models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class RecommendationType(str, Enum):
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    WORKFLOW = "workflow"
    CODE_QUALITY = "code_quality"
    ACCURACY = "accuracy"
    TOOLING = "tooling"


@dataclass
class EvolutionRecommendation:
    rec_id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    description: str = ""
    recommendation_type: RecommendationType = RecommendationType.PERFORMANCE
    target_module: str = ""
    estimated_gain_pct: float = 0.0
    confidence: float = 0.95
    evidence: str = ""
    action_items: List[str] = field(default_factory=list)
    applied: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rec_id": self.rec_id,
            "title": self.title,
            "description": self.description,
            "recommendation_type": self.recommendation_type.value if isinstance(self.recommendation_type, RecommendationType) else str(self.recommendation_type),
            "target_module": self.target_module,
            "estimated_gain_pct": round(float(self.estimated_gain_pct), 2),
            "confidence": round(float(self.confidence), 4),
            "evidence": self.evidence,
            "action_items": list(self.action_items),
            "applied": self.applied,
            "created_at": self.created_at,
        }
