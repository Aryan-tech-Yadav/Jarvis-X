class MemoryCompressor:
    """Produces a loss-aware compact representation without mutating source data."""

    def __init__(self, max_entries=10, max_characters=1000):
        self.max_entries = max(1, max_entries)
        self.max_characters = max(1, max_characters)

    def compress(self, entries):
        values = list(entries or [])
        if len(values) <= self.max_entries:
            return {"compressed": False, "entries": values, "summary": ""}
        old, recent = values[:-self.max_entries], values[-self.max_entries:]
        text = " | ".join(str(item.get("content", item)) for item in old)
        return {"compressed": True, "entries": recent, "summary": text[:self.max_characters], "source_count": len(old)}
