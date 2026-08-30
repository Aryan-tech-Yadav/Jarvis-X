from abc import ABC


class LifecycleComponent(ABC):
    """Optional lifecycle protocol for managers that participate in a run."""

    def initialize(self, context=None):
        return True

    def validate(self, context=None):
        return True

    def cleanup(self, context=None):
        return True

    def shutdown(self, context=None):
        return self.cleanup(context)
