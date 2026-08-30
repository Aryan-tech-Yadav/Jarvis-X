"""Engineering graph relationship."""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class EngineeringEdge:
    source: str
    target: str
    relation: str
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"source": self.source, "target": self.target,
                "relation": self.relation, "properties": dict(self.properties)}

