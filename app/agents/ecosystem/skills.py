"""Skill declaration for ecosystem agents."""

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class AgentSkills:
    names: Tuple[str, ...] = field(default_factory=tuple)

    def supports(self, skill: str) -> bool:
        return skill.casefold() in {name.casefold() for name in self.names}

