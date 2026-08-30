from app.capabilities.capability_registry import CapabilityRegistry


class CapabilityMatcher:
    def __init__(self, registry=None):
        self.registry = registry or CapabilityRegistry()

    def match(self, request):
        return self.registry.match(request)

    def best(self, request):
        matches = [item for item in self.match(request) if item.enabled]
        return matches[0] if matches else None