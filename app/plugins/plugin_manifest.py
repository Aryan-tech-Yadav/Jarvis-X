from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class PluginManifest:
    name: str
    version: str = "1.0.0"
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)