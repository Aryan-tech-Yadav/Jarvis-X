from dataclasses import dataclass, field
from typing import Any, Dict, List
from uuid import uuid4

from app.eos.goal import Goal


@dataclass
class Mission:
    goal: Goal
    mission_id: str = field(default_factory=lambda: f"mission-{uuid4().hex[:12]}")
    status: str = "created"
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
