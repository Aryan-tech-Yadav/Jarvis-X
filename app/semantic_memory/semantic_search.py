from app.semantic_memory.validators import normalized_text


class SemanticSearch:
    def __init__(self, store, ranker):
        self.store = store
        self.ranker = ranker

    def search(self, query, limit=5, min_score=0.0):
        return self.ranker.rank(normalized_text(query, "query"), self.store.all(), limit, min_score)
