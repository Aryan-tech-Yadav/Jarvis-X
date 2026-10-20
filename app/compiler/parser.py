"""Parser and intermediate representation for engineering specifications."""

from dataclasses import dataclass, field
from typing import Dict, List

from .lexer import Lexer


@dataclass
class EngineeringSpec:
    project: str
    modules: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    database: str = ""
    auth: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {"project": self.project, "modules": list(self.modules),
                "roles": list(self.roles), "database": self.database, "auth": self.auth}


class DSLParser:
    def __init__(self, lexer=None):
        self.lexer = lexer or Lexer()

    def parse(self, source: str) -> EngineeringSpec:
        tokens = self.lexer.tokenize(source)
        if not tokens:
            raise ValueError("DSL cannot be empty")
        values = {"project": "", "modules": [], "roles": [], "database": "", "auth": ""}
        for token in tokens:
            key = {"PROJECT": "project", "MODULE": "modules", "ROLE": "roles",
                   "DATABASE": "database", "AUTH": "auth"}[token.kind]
            if key in ("modules", "roles"):
                values[key].append(token.value)
            else:
                if values[key]:
                    raise ValueError(f"Duplicate {token.kind} on line {token.line}")
                values[key] = token.value
        if not values["project"]:
            raise ValueError("DSL requires PROJECT")
        return EngineeringSpec(**values)

