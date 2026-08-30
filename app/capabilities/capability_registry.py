class CapabilityRegistry:
    def __init__(self):
        self._capabilities = {}

    def register(self, capability):
        self._capabilities[capability.name] = capability

    def remove(self, name):
        return self._capabilities.pop(name, None)

    def get(self, name):
        return self._capabilities.get(name)

    def list(self):
        return list(self._capabilities.values())

    def search(self, query):
        terms = str(query).casefold().split()
        return [item for item in self.list() if any(term in f"{item.name} {item.description}".casefold() for term in terms)]

    def match(self, query):
        return sorted(self.search(query), key=lambda item: item.priority, reverse=True)