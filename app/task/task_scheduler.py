from app.task.task_graph import TaskGraph
from app.task.task_priority import TaskPriority


class TaskScheduler:
    def __init__(self, graph=None, priority=None):
        self.graph = graph or TaskGraph()
        self.priority = priority or TaskPriority()

    def submit(self, task):
        return self.graph.add(task)

    def next_batch(self):
        tasks = self.priority.sort(self.graph.ready())
        for task in tasks:
            task.status = "running"
            task.attempts += 1
        return tasks

    def complete(self, task_id, result=None):
        return self.graph.complete(task_id, result)

    def fail(self, task_id, result=None):
        task = self.graph.tasks[task_id]
        task.result = result
        if task.can_retry():
            task.status = "pending"
        else:
            task.status = "failed"
        return task

    def resume(self):
        for task in self.graph.tasks.values():
            if task.status == "running":
                task.status = "pending"
        return self.next_batch()
