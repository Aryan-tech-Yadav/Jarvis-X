from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class TaskResult:
    task_id: str
    success: bool
    output: Any = None
    error: Optional[str] = None

    def to_dict(self):
        return {"task_id": self.task_id, "success": self.success, "output": self.output, "error": self.error}