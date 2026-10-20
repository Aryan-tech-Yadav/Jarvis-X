"""Typed result contract for EOS-dispatched work."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AgentResult:
    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    agent: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_value(cls, value: Any, agent: str = "") -> "AgentResult":
        if isinstance(value, cls):
            if agent and not value.agent:
                value.agent = agent
            return value
        if isinstance(value, dict):
            return cls(
                success=bool(value.get("success", False)),
                output=value.get("output"),
                error=value.get("error"),
                execution_time=float(value.get("execution_time", value.get("duration", 0.0)) or 0.0),
                agent=agent or str(value.get("agent", "")),
                metadata=dict(value.get("metadata", {})),
            )
        return cls(success=True, output=value, agent=agent)
