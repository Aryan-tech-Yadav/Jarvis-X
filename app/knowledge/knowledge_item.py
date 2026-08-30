from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class KnowledgeItem:
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    item_id: str = ""

    def to_dict(self):
        return {"id": self.item_id, "text": self.text, "metadata": self.metadata}