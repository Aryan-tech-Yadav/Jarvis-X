"""Lexer for the line-oriented engineering DSL."""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    line: int


class Lexer:
    KEYWORDS = {"PROJECT", "MODULE", "ROLE", "DATABASE", "AUTH"}

    def tokenize(self, source: str) -> List[Token]:
        if not isinstance(source, str):
            raise TypeError("DSL source must be a string")
        tokens = []
        for line_number, raw_line in enumerate(source.splitlines(), 1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(maxsplit=1)
            keyword = parts[0].upper()
            if keyword not in self.KEYWORDS or len(parts) != 2 or not parts[1].strip():
                raise ValueError(f"Invalid DSL statement on line {line_number}")
            tokens.append(Token(keyword, parts[1].strip(), line_number))
        return tokens

