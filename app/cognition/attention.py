"""Bounded attention selection over perceived information."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List


@dataclass
class AttentionItem:
    value: Any
    score: float
    reason: str = ""


class AttentionEngine:
    def focus(self, items: Iterable[Any], query: str = "", limit: int = 10) -> List[AttentionItem]:
        if limit < 0:
            raise ValueError("Attention limit cannot be negative")
        terms = set(str(query).casefold().split())
        scored = []
        for index, item in enumerate(items):
            text = str(item).casefold()
            overlap = sum(term in text for term in terms)
            score = float(overlap * 10 + (1.0 / (index + 1)))
            scored.append(AttentionItem(item, score, "query overlap" if overlap else "recency"))
        scored.sort(key=lambda entry: (-entry.score, str(entry.value)))
        return scored[:limit]

