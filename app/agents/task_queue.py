import heapq


class AgentTaskQueue:
    def __init__(self):
        self._items = []
        self._sequence = 0

    def enqueue(self, task):
        if not hasattr(task, "priority"):
            raise TypeError("Task must expose a priority")
        task.status = "pending"
        self._sequence += 1
        heapq.heappush(self._items, (-task.priority, self._sequence, task))

    def dequeue(self):
        if not self._items:
            return None
        task = heapq.heappop(self._items)[2]
        task.status = "running"
        return task

    def complete(self, task, result=None):
        task.status = "completed"
        task.result = result
        return task

    def fail(self, task, result=None):
        task.status = "failed"
        task.result = result
        return task

    def peek(self):
        return self._items[0][2] if self._items else None

    def clear(self):
        self._items.clear()

    def __len__(self):
        return len(self._items)
