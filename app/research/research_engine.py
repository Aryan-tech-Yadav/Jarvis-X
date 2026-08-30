from .best_practices import BestPractices
from .citation_builder import CitationBuilder
from .research_cache import ResearchCache


class ResearchEngine:
    """Returns vetted baseline practices. Network research remains an explicit caller action."""

    def __init__(self, practices=None, cache=None, citations=None):
        self.practices = practices or BestPractices()
        self.cache = cache or ResearchCache()
        self.citations = citations or CitationBuilder()

    def research(self, requirements, architecture=None):
        key = tuple(sorted(requirements.get("features", ())))
        cached = self.cache.get(key)
        if cached is not None:
            return dict(cached, cache_hit=True)
        findings = self.practices.for_features(requirements.get("features", ()))
        result = {"findings": findings, "citations": self.citations.build(findings), "cache_hit": False}
        return self.cache.set(key, result)
