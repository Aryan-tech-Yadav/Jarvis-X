from app.learning.scorer import PatternScorer


class PatternRanking:
    def __init__(self, scorer=None):
        self.scorer = scorer or PatternScorer()

    def rank(self, patterns, query, limit=5):
        ranked = [(self.scorer.score(pattern, query), pattern) for pattern in patterns]
        ranked.sort(key=lambda pair: pair[0], reverse=True)
        return [pattern for score, pattern in ranked if score > 0][:max(0, limit)]