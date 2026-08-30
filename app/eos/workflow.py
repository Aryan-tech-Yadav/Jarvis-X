from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


@dataclass(frozen=True)
class WorkflowStage:
    name: str
    state: str
    handler: Callable[[Any], Any]


class Workflow:
    def __init__(self, stages: List[WorkflowStage] | None = None):
        self.stages = list(stages or [])

    def add(self, name: str, state: str, handler: Callable[[Any], Any]) -> None:
        self.stages.append(WorkflowStage(name, state, handler))

    def names(self) -> List[str]:
        return [stage.name for stage in self.stages]
