import time


class ToolCache:
    def __init__(self, default_ttl=60):
        self.default_ttl = default_ttl
        self._values = {}

    def get(self, key):
        value = self._values.get(str(key))
        if value is None or value[0] <= time.time():
            self._values.pop(str(key), None)
            return None
        return value[1]

    def set(self, key, value, ttl=None):
        self._values[str(key)] = (time.time() + (self.default_ttl if ttl is None else ttl), value)
        return value

    def clear(self):
        self._values.clear()
