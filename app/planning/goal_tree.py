from dataclasses import dataclass, field
from typing import List


@dataclass
class GoalNode:
    name: str
    children: List["GoalNode"] = field(default_factory=list)
    completed: bool = False

    def add(self, child):
        self.children.append(child)

    def flatten(self):
        return [self] + [item for child in self.children for item in child.flatten()]