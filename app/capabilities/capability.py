from dataclasses import dataclass
from typing import Any


@dataclass
class Capability:
    name: str
    description: str
    provider: Any
    priority: int = 0
    enabled: bool = True