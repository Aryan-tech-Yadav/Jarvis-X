from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class AgentTask:
    title: str
    agent: str
    priority: int = 0
    status: str = "pending"
    result: Any = None
    history: List[Any] = field(default_factory=list)