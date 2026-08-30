class StageRegistry:
    """Ordered registry with duplicate and contract protection."""

    def __init__(self):
        self._stages = {}

    def register(self, stage):
        required = ("name", "validate", "execute", "rollback", "metrics")
        if any(not hasattr(stage, attribute) for attribute in required):
            raise TypeError("Stage does not implement the PipelineStage contract")
        name = str(stage.name or "").strip()
        if not name:
            raise ValueError("Stage name cannot be empty")
        if name in self._stages:
            raise ValueError("Stage already registered: " + name)
        self._stages[name] = stage
        return stage

    def get(self, name):
        return self._stages.get(name)

    def stages(self):
        return tuple(self._stages.values())

    def names(self):
        return tuple(self._stages)
