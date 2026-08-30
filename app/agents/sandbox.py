"""Path boundary for dynamically spawned agents."""

from pathlib import Path


class AgentSandbox:
    def __init__(self, root: str):
        self.root = Path(root).resolve()

    def path(self, relative_path: str) -> Path:
        if not relative_path or not relative_path.strip():
            raise ValueError("Sandbox path cannot be empty")
        candidate = (self.root / relative_path).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise PermissionError("Agent path escapes sandbox")
        return candidate

    def contains(self, target: str) -> bool:
        try:
            self.path(target)
            return True
        except (PermissionError, ValueError):
            return False

