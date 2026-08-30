from dataclasses import dataclass


@dataclass
class AgentCapability:
    name: str
    priority: int = 0
    confidence: float = 0.0