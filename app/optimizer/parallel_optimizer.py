class ParallelOptimizer:
    def groups(self, ordered_steps):
        groups = []
        current = []
        completed = set()
        for step in ordered_steps:
            value = dict(step) if isinstance(step, dict) else {"name": str(step)}
            dependencies = set(value.get("dependencies", ()))
            if current and (not value.get("parallelizable", False) or dependencies - completed):
                groups.append(current)
                completed.update(item["name"] for item in current)
                current = []
            current.append(value)
            if not value.get("parallelizable", False):
                groups.append(current)
                completed.update(item["name"] for item in current)
                current = []
        if current:
            groups.append(current)
        return groups
