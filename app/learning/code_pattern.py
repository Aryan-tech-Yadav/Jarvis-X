from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class CodePattern:
    name: str
    code: str
    language: str = "python"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {"type": "code", "name": self.name, "code": self.code, "language": self.language, "tags": self.tags, "metadata": self.metadata}