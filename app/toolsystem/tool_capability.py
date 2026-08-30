"""Tool capability, permission, and risk models for intelligent tool selection."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ToolRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ToolCapability:
    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    cost: float = 0.0  # Estimated resource/token cost
    risk: ToolRisk = ToolRisk.LOW
    timeout_sec: float = 30.0
    permissions: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": dict(self.input_schema),
            "output_schema": dict(self.output_schema),
            "cost": self.cost,
            "risk": self.risk.value if isinstance(self.risk, ToolRisk) else str(self.risk),
            "timeout_sec": self.timeout_sec,
            "permissions": list(self.permissions),
            "tags": list(self.tags),
        }
