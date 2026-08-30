from app.semantic_memory.semantic_similarity import SemanticSimilarity


class SemanticRanker:
    def __init__(self, similarity=None):
        self.similarity = similarity or SemanticSimilarity()

    def rank(self, query, memories, limit=5, min_score=0.0):
        if not isinstance(limit, int) or limit < 0:
            raise ValueError("limit must be a non-negative integer")
        ranked = []
        for memory in memories:
            relevance = self.similarity.score(query, memory)
            score = 0.75 * relevance + 0.15 * memory.importance + 0.10 * memory.confidence
            if score >= min_score:
                ranked.append((score, relevance, memory))
        ranked.sort(key=lambda item: (item[0], item[2].updated_at, item[2].memory_id), reverse=True)
        return [
            {"score": round(score, 6), "relevance": round(relevance, 6), **memory.to_dict()}
            for score, relevance, memory in ranked[:limit]
        ]
