from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ExecutionContext:
    goal: str
    current_step: str = ""
    completed_steps: List[str] = field(default_factory=list)
    project_path: Optional[str] = None
    memory: Any = None
    conversation: List[Dict[str, Any]] = field(default_factory=list)
    retry_count: int = 0
    current_tool: Optional[str] = None
    observations: List[Any] = field(default_factory=list)