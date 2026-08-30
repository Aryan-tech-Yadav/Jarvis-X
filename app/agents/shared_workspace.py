from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class SharedWorkspace:
    goal: str
    project_summary: Any = None
    plan: Any = None
    progress: Dict[str, Any] = field(default_factory=dict)
    conversation: List[Any] = field(default_factory=list)
    memory: Any = None
    observations: List[Any] = field(default_factory=list)
    changed_files: List[str] = field(default_factory=list)
    open_issues: List[str] = field(default_factory=list)