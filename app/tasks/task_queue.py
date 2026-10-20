import uuid
from collections import deque

from app.tasks.task_status import TaskStatus


class TaskQueue:
    def __init__(self):
        self._pending = deque()
        self._tasks = {}
        self._history = []

    def submit(self, task):
        task_id = getattr(task, "task_id", None) or str(uuid.uuid4())
        task.task_id = task_id
        task.status = TaskStatus.QUEUED.value
        self._tasks[task_id] = task
        self._pending.append(task_id)
        return task_id

    def next(self):
        while self._pending:
            task = self._tasks[self._pending.popleft()]
            if task.status == TaskStatus.QUEUED.value:
                task.status = TaskStatus.RUNNING.value
                return task
        return None

    def complete(self, task_id, result=None):
        return self._finish(task_id, TaskStatus.COMPLETED, result)

    def fail(self, task_id, result=None):
        return self._finish(task_id, TaskStatus.FAILED, result)

    def cancel(self, task_id):
        task = self._tasks.get(task_id)
        if task and task.status == TaskStatus.QUEUED.value:
            task.status = TaskStatus.CANCELLED.value
            self._history.append(task)
            return True
        return False

    def status(self, task_id):
        task = self._tasks.get(task_id)
        return task.status if task else None

    def get(self, task_id):
        return self._tasks.get(task_id)

    def history(self):
        return list(self._history)

    def _finish(self, task_id, status, result):
        task = self._tasks.get(task_id)
        if not task:
            return False
        task.status = status.value
        task.result = result
        self._history.append(task)
        return True