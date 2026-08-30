import time

from app.memory.memory_index import MemoryIndex


class MemoryRanker:
    def score(self, entry, query="", now=None):
        now = time.time() if now is None else now
        matches = len(MemoryIndex.tokens(entry.get("content", "")) & MemoryIndex.tokens(query))
        age_hours = max(0.0, (now - entry.get("created_at", now)) / 3600)
        recency = 1 / (1 + age_hours / 24)
        return matches * 10 + entry.get("priority", 0) * 2 + entry.get("importance", 0.0) * 5 + recency

    def rank(self, entries, query="", limit=5):
        return sorted(entries, key=lambda item: self.score(item, query), reverse=True)[:max(0, limit)]
