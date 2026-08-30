from app.knowledge.embedding_manager import EmbeddingManager


class SemanticSimilarity:
    """Deterministic lexical semantic similarity suitable for offline operation."""

    def __init__(self, embeddings=None):
        self.embeddings = embeddings or EmbeddingManager()

    def score(self, query, memory):
        content_score = self.embeddings.similarity(
            self.embeddings.embed(query), self.embeddings.embed(memory.content)
        )
        tag_score = self.embeddings.similarity(
            self.embeddings.embed(query), self.embeddings.embed(" ".join(memory.tags))
        )
        return 0.8 * content_score + 0.2 * tag_score
