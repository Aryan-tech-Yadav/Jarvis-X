class StrategySelector:
    """Selects a deterministic winner: quality first, then risk and speed."""

    def rank(self, results):
        return sorted(results, key=lambda item: (-item.score, item.risk, item.estimated_minutes, item.name.casefold()))

    def select(self, results):
        ranked = self.rank(results)
        return ranked[0] if ranked else None
