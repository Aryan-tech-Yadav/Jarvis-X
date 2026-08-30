from app.semantic_memory.models import SemanticMemory
from app.semantic_memory.semantic_export import SemanticExport
from app.semantic_memory.semantic_ranker import SemanticRanker
from app.semantic_memory.semantic_relationship import SemanticRelationship
from app.semantic_memory.semantic_search import SemanticSearch
from app.semantic_memory.semantic_statistics import SemanticStatistics
from app.semantic_memory.semantic_store import SemanticStore
from app.semantic_memory.validators import normalized_text


class SemanticMemoryManager:
    """Application facade for storing and retrieving engineering experience."""

    def __init__(self, store=None, ranker=None, relationships=None, statistics=None, exporter=None):
        self.store = store or SemanticStore()
        self.ranker = ranker or SemanticRanker()
        self.searcher = SemanticSearch(self.store, self.ranker)
        self.relationships = relationships or SemanticRelationship()
        self.statistics_calculator = statistics or SemanticStatistics()
        self.exporter = exporter or SemanticExport()

    def remember(self, content, *, memory_type="experience", tags=None, importance=0.5,
                 confidence=0.5, metadata=None):
        content = normalized_text(content)
        memory_type = normalized_text(memory_type, "memory_type").casefold()
        existing = self.store.find_duplicate(content, memory_type)
        if existing is not None:
            return existing
        memory = SemanticMemory(
            content=content,
            memory_type=memory_type,
            tags=tags or (),
            importance=importance,
            confidence=confidence,
            metadata=metadata or {},
        )
        return self.store.add(memory)

    def record_outcome(self, goal, success, *, tags=None, confidence=0.8, metadata=None):
        metadata = {**(metadata or {}), "success": bool(success)}
        return self.remember(
            goal,
            memory_type="success" if success else "failure",
            tags=tags or ("execution",),
            importance=0.8 if success else 0.9,
            confidence=confidence,
            metadata=metadata,
        )

    def search(self, query, limit=5, min_score=0.0):
        return self.searcher.search(query, limit, min_score)

    def context_for(self, goal, limit=5):
        return self.search(goal, limit=limit, min_score=0.05)

    def related(self, memory_id, limit=5):
        memory = self.store.get(memory_id)
        return self.relationships.related(memory, self.store.all(), limit) if memory else []

    def statistics(self):
        return self.statistics_calculator.calculate(self.store.all())

    def export(self):
        return self.exporter.export(self.store.all(), self.statistics())
