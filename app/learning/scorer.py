class PatternScorer:
    def score(self, pattern, query):
        text = str(pattern).casefold()
        terms = set(str(query).casefold().split())
        return sum(term in text for term in terms)