class KnowledgeSearch:
    def __init__(self, store, index, ranker):
        self.store = store
        self.index = index
        self.ranker = ranker

    def search(self, query, limit=5):
        identifiers = self.index.find(query)
        facts = [self.store.get(identifier) for identifier in identifiers]
        return self.ranker.rank([fact for fact in facts if fact], query, limit)
