from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ExecutionContext:
    mission: Any
    files: List[str] = field(default_factory=list)
    memory: Dict[str, Any] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    status: str = "idle"
    data: Dict[str, Any] = field(default_factory=dict)

    def record(self, stage: str, result: Any) -> None:
        self.data[stage] = result
        self.logs.append(f"{stage}: completed")
