from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(init=False)
class Action:
    tool: str
    name: str
    arguments: Dict[str, Any]

    def __init__(self, tool, action=None, arguments=None, name=None):
        self.tool = tool
        self.name = action if action is not None else (name or "")
        self.arguments = arguments or {}

    @property
    def action(self):
        return self.name

    def to_dict(self):
        return {"tool": self.tool, "action": self.name, "input": self.arguments}