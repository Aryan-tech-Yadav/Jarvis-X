from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Goal:
    text: str
    analysis: Dict[str, Any] = field(default_factory=dict)
    deliverables: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("Goal cannot be empty")
        self.text = self.text.strip()
