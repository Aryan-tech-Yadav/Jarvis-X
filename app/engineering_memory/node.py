"""Engineering graph node."""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class EngineeringNode:
    node_id: str
    label: str
    node_type: str
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"node_id": self.node_id, "label": self.label,
                "node_type": self.node_type, "properties": dict(self.properties)}

