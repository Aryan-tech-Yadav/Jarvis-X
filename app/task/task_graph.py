class TaskGraph:
    def __init__(self):
        self.tasks = {}

    def add(self, task):
        if task.task_id in self.tasks:
            raise ValueError(f"Duplicate task: {task.task_id}")
        missing = set(task.dependencies) - set(self.tasks)
        if missing:
            raise ValueError(f"Unknown dependencies: {', '.join(sorted(missing))}")
        self.tasks[task.task_id] = task
        if self._has_cycle():
            self.tasks.pop(task.task_id)
            raise ValueError("Task dependencies contain a cycle")
        return task

    def complete(self, task_id, result=None):
        task = self.tasks[task_id]
        task.status, task.result = "completed", result
        return task

    def ready(self):
        return [task for task in self.tasks.values() if task.status == "pending" and all(self.tasks[item].status == "completed" for item in task.dependencies)]

    def levels(self):
        remaining = set(self.tasks)
        completed = set()
        levels = []
        while remaining:
            level = [identifier for identifier in remaining if set(self.tasks[identifier].dependencies) <= completed]
            if not level:
                raise ValueError("Task dependencies contain a cycle")
            levels.append(sorted(level))
            remaining.difference_update(level)
            completed.update(level)
        return levels

    def _has_cycle(self):
        try:
            self.levels()
            return False
        except ValueError:
            return True
