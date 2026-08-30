from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class AgentContext:
    goal: str
    project: Any = None
    current_file: Any = None
    conversation: List[Any] = field(default_factory=list)
    memory: Any = None
    observations: List[Any] = field(default_factory=list)
    progress: Any = None
    shared_notes: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)