class TaskPriority:
    @staticmethod
    def score(task):
        return int(getattr(task, "priority", 0)) + (100 if not getattr(task, "dependencies", ()) else 0)

    def sort(self, tasks):
        return sorted(tasks, key=lambda task: (-self.score(task), task.created_at))
