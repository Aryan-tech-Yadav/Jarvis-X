class TaskWorker:
    def __init__(self, queue, handler):
        self.queue = queue
        self.handler = handler

    def run_once(self):
        task = self.queue.next()
        if task is None:
            return None
        try:
            result = self.handler(task)
            self.queue.complete(task.task_id, result)
        except Exception as error:
            result = {"success": False, "error": str(error)}
            self.queue.fail(task.task_id, result)
        return result