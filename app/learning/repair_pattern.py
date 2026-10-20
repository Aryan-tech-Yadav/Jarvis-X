from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class RepairPattern:
    error: str
    repair: str
    success: bool = True
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {"type": "repair", "error": self.error, "repair": self.repair, "success": self.success, "tags": self.tags, "metadata": self.metadata}