from app.knowledge.knowledge_index import KnowledgeIndex


class KnowledgeRanker:
    def score(self, fact, query):
        matches = len(KnowledgeIndex.tokens(fact.get("text", "")) & KnowledgeIndex.tokens(query))
        topic_matches = len(set(fact.get("topics", ())) & KnowledgeIndex.tokens(query))
        return matches * 3 + topic_matches * 5 + fact.get("confidence", 0.0)

    def rank(self, facts, query, limit=5):
        return sorted(facts, key=lambda fact: self.score(fact, query), reverse=True)[:max(0, limit)]
