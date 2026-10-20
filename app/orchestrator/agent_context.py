from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class AgentContext:
    goal: str
    project: Any = None
    memory: Any = None
    progress: Any = None
    task: Any = None
    reasoning: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    current_file: Any = None
    conversation: list = field(default_factory=list)
    observations: list = field(default_factory=list)
    shared_notes: Dict[str, Any] = field(default_factory=dict)