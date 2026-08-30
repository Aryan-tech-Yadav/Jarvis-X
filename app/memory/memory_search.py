from app.memory.memory_ranker import MemoryRanker


class MemorySearch:
    def __init__(self, index, ranker=None):
        self.index = index
        self.ranker = ranker or MemoryRanker()

    def search(self, query, limit=5):
        if not isinstance(query, str) or not query.strip():
            return []
        return self.ranker.rank(self.index.candidates(query), query, limit)
