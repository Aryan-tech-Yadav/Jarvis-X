"""Capability declarations used by agent selection."""

from dataclasses import dataclass, field
from typing import Iterable, Tuple


@dataclass(frozen=True)
class Capabilities:
    names: Tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_values(cls, values: Iterable[str]) -> "Capabilities":
        return cls(tuple(dict.fromkeys(str(value).casefold() for value in values)))

    def supports(self, capability: str) -> bool:
        return capability.casefold() in self.names

