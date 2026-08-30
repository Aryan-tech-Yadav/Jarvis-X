from dataclasses import dataclass
from typing import Any


@dataclass
class Artifact:
    name: str
    content: Any = None
    category: str = "code"
