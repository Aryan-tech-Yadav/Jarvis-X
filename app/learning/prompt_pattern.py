from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class PromptPattern:
    task: str
    prompt: str
    outcome: str = "success"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {"type": "prompt", "task": self.task, "prompt": self.prompt, "outcome": self.outcome, "tags": self.tags, "metadata": self.metadata}