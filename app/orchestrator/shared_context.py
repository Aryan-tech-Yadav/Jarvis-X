from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.context import JarvisContext


@dataclass
class SharedContext(JarvisContext):
    base_path: Optional[str] = None
    plan: Any = None
    project: Any = None
    files: List[str] = field(default_factory=list)
    progress: List[Dict[str, Any]] = field(default_factory=list)
    validation: Dict[str, Any] = field(default_factory=dict)
    reflection: Dict[str, Any] = field(default_factory=dict)
    critic: Dict[str, Any] = field(default_factory=dict)
    research: Dict[str, Any] = field(default_factory=dict)
    learning: Dict[str, Any] = field(default_factory=dict)
    tool_outputs: List[Any] = field(default_factory=list)
    outputs: Dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        super().__post_init__()
        if self.project_path is None:
            self.project_path = self.base_path
        elif self.base_path is None:
            self.base_path = self.project_path

    def add_progress(self, agent, result):
        self.progress.append({"agent": agent, "result": result})
        self.outputs[agent] = result.get("output") if isinstance(result, dict) else result

    def as_dict(self):
        return {
            **super().as_dict(),
            "base_path": self.base_path,
            "plan": self.plan,
            "project": self.project,
            "files": self.files,
            "progress": self.progress,
            "validation": self.validation,
            "reflection": self.reflection,
            "critic": self.critic,
            "research": self.research,
            "learning": self.learning,
            "tool_outputs": self.tool_outputs,
            "outputs": self.outputs,
        }
