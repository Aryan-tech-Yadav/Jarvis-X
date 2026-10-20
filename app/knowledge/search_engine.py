from app.knowledge.vector_store import VectorStore


class KnowledgeSearchEngine:
    def __init__(self, store=None):
        self.store = store or VectorStore()

    def search(self, query, limit=5, threshold=0.0):
        return self.store.search(query, limit, threshold)


SearchEngine = KnowledgeSearchEngine