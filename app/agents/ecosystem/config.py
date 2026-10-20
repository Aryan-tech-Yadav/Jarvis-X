"""Configuration value object for AMOS agents."""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class AgentConfig:
    enabled: bool = True
    settings: Dict[str, Any] = field(default_factory=dict)

