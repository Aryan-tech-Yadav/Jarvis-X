from app.knowledge.knowledge_cache import KnowledgeCache
from app.knowledge.knowledge_index import KnowledgeIndex
from app.knowledge.knowledge_ranker import KnowledgeRanker
from app.knowledge.knowledge_search import KnowledgeSearch
from app.knowledge.knowledge_store import KnowledgeStore


class KnowledgeBase:
    """Small semantic fact graph, complementary to the existing document vector store."""

    def __init__(self, store=None, index=None, ranker=None, cache=None):
        self.store = store or KnowledgeStore()
        self.index = index or KnowledgeIndex()
        self.ranker = ranker or KnowledgeRanker()
        self.cache = cache or KnowledgeCache()
        self.searcher = KnowledgeSearch(self.store, self.index, self.ranker)

    def add_fact(self, text, *, category="general", topics=None, confidence=0.5, metadata=None):
        fact = self.store.add(text, category=category, topics=topics, confidence=confidence, metadata=metadata)
        self.index.add(fact)
        self.cache.clear()
        return fact

    def search(self, query, limit=5):
        key = f"{query}:{limit}"
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        result = self.searcher.search(query, limit)
        self.cache.set(key, result)
        return result

    def related(self, fact_id, limit=5):
        fact = self.store.get(fact_id)
        if fact is None:
            return []
        related = [self.store.get(identifier) for identifier in self.index.related_ids(fact)]
        return self.ranker.rank([item for item in related if item], " ".join(fact.get("topics", ())), limit)

    def extract_facts(self, text, category="general", confidence=0.5):
        """Turn a short text into independently searchable sentence-level facts."""
        import re

        sentences = [item.strip() for item in re.split(r"[.!?]+", str(text)) if item.strip()]
        return [self.add_fact(sentence, category=category, topics=KnowledgeIndex.tokens(sentence), confidence=confidence) for sentence in sentences]
