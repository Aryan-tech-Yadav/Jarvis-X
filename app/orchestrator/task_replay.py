from app.orchestrator.task import Task


class TaskReplay:
    def __init__(self, task):
        if not isinstance(task, Task):
            raise TypeError("task must be a Task")
        self.task = task

    def events(self):
        return list(self.task.history)

    def replay(self):
        for event in self.events():
            yield event

    def to_dict(self):
        return self.task.to_dict()