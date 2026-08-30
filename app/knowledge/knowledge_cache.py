import time


class KnowledgeCache:
    def __init__(self, ttl=300):
        self.ttl = ttl
        self._values = {}
        self.hits = 0

    def get(self, key):
        item = self._values.get(str(key).casefold())
        if item is None or item[0] <= time.time():
            self._values.pop(str(key).casefold(), None)
            return None
        self.hits += 1
        return list(item[1])

    def set(self, key, value):
        self._values[str(key).casefold()] = (time.time() + self.ttl, list(value))

    def clear(self):
        self._values.clear()
