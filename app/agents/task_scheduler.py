class TaskScheduler:
    def __init__(self, queue, dispatcher):
        self.queue = queue
        self.dispatcher = dispatcher

    def run_once(self):
        task = self.queue.dequeue()
        if task is None:
            return None
        task.status = "running"
        result = self.dispatcher.dispatch(task)
        task.result = result
        task.status = "completed" if result.get("success") else "failed"
        return result