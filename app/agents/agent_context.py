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

    # Compatibility fields for project-oriented agents.
    project_path: str = ""
    current_task: str = ""
    logs: List[str] = field(default_factory=list)
    completed_tasks: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def add_log(self, message: str) -> None:
        if message:
            self.logs.append(message)

    def add_completed_task(self, task: str) -> None:
        if task and task not in self.completed_tasks:
            self.completed_tasks.append(task)

    def set_metric(self, key: str, value: Any) -> None:
        self.metrics[key] = value
