from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class RollbackAction:
    name: str
    undo: Callable[[], Any]


class RollbackManager:
    def __init__(self):
        self._actions: list[RollbackAction] = []

    def register(self, name: str, undo: Callable[[], Any]) -> None:
        self._actions.append(RollbackAction(name, undo))

    def rollback(self) -> list[str]:
        completed = []
        for action in reversed(self._actions):
            action.undo()
            completed.append(action.name)
        self._actions.clear()
        return completed
