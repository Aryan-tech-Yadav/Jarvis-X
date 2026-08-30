import copy
import hashlib
import time


class ReasoningCache:
    def __init__(self, default_ttl=300):
        self.default_ttl = default_ttl
        self._values = {}

    def key(self, goal, context=""):
        payload = f"{str(goal).strip()}\n{str(context).strip()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(self, goal, context=""):
        key = self.key(goal, context)
        item = self._values.get(key)
        if item is None or item[0] <= time.time():
            self._values.pop(key, None)
            return None
        return copy.deepcopy(item[1])

    def set(self, goal, context, result, ttl=None):
        self._values[self.key(goal, context)] = (time.time() + (self.default_ttl if ttl is None else ttl), copy.deepcopy(result))
        return result

    def clear(self):
        self._values.clear()
