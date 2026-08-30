import time


class MemoryCleaner:
    def __init__(self, max_age_seconds=None, max_entries=None):
        self.max_age_seconds = max_age_seconds
        self.max_entries = max_entries

    def clean(self, entries, now=None):
        now = time.time() if now is None else now
        unique = {}
        for entry in entries or []:
            content = str(entry.get("content", "")).casefold().strip()
            if not content or content in unique:
                continue
            if self.max_age_seconds is not None and now - entry.get("created_at", now) > self.max_age_seconds:
                continue
            unique[content] = entry
        cleaned = list(unique.values())
        cleaned.sort(key=lambda item: (item.get("priority", 0), item.get("importance", 0), item.get("created_at", 0)), reverse=True)
        return cleaned[:self.max_entries] if self.max_entries is not None else cleaned
