import re
from collections import defaultdict


class KnowledgeIndex:
    def __init__(self):
        self._topics = defaultdict(set)
        self._terms = defaultdict(set)

    def add(self, fact):
        fact_id = fact["id"]
        for topic in fact.get("topics", ()):
            self._topics[topic.casefold()].add(fact_id)
        self._topics[fact.get("category", "general").casefold()].add(fact_id)
        for term in self.tokens(fact.get("text", "")):
            self._terms[term].add(fact_id)

    def find(self, query):
        identifiers = set()
        for term in self.tokens(query):
            identifiers.update(self._topics.get(term, ()))
            identifiers.update(self._terms.get(term, ()))
        return identifiers

    def related_ids(self, fact):
        identifiers = set()
        for topic in fact.get("topics", ()) + [fact.get("category", "general")]:
            identifiers.update(self._topics.get(topic.casefold(), ()))
        identifiers.discard(fact["id"])
        return identifiers

    @staticmethod
    def tokens(value):
        return set(re.findall(r"[a-z0-9_]+", str(value).casefold()))
