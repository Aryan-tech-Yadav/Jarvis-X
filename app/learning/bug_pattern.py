from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class BugPattern:
    error: str
    cause: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {"type": "bug", "error": self.error, "cause": self.cause, "tags": self.tags, "metadata": self.metadata}