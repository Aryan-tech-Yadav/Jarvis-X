class StepMerger:
    """Merges adjacent low-risk validation work into one observable step."""

    MERGEABLE = {"validate", "test", "testing", "review"}

    def merge(self, steps):
        merged = []
        pending = []
        for step in steps:
            name = self._name(step)
            if name in self.MERGEABLE:
                pending.append(step)
                continue
            if pending:
                merged.append(self._combined(pending))
                pending = []
            merged.append(step)
        if pending:
            merged.append(self._combined(pending))
        return merged

    @staticmethod
    def _name(step):
        return str(step.get("name", "") if isinstance(step, dict) else step).casefold()

    @staticmethod
    def _combined(steps):
        names = [item.get("name", "") if isinstance(item, dict) else str(item) for item in steps]
        preferred_order = {"validate": 0, "test": 1, "testing": 1, "review": 2}
        names.sort(key=lambda name: (preferred_order.get(name.casefold(), 99), name.casefold()))
        return {"name": " + ".join(names), "merged": names, "parallelizable": True}
