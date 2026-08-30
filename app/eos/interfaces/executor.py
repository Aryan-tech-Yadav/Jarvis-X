from typing import Any, Protocol


class Executor(Protocol):
    def execute(self, context: Any) -> Any:
        ...
