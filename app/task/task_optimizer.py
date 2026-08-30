class TaskOptimizer:
    def estimate(self, tasks):
        """Estimate wall time assuming tasks in the same dependency level run together."""
        levels = {}
        for task in tasks:
            level = len(task.dependencies)
            levels.setdefault(level, []).append(float(task.eta_seconds or 0))
        return sum(max(values) for values in levels.values()) if levels else 0.0

    def optimize(self, tasks):
        return sorted(tasks, key=lambda task: (-task.priority, task.eta_seconds, task.created_at))
