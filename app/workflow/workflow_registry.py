class WorkflowRegistry:
    def __init__(self, handlers=None):
        self._handlers = dict(handlers or {})

    def register(self, step_id, handler):
        if not isinstance(step_id, str) or not step_id.strip():
            raise ValueError("step_id must be a non-empty string")
        if not callable(handler):
            raise TypeError("handler must be callable")
        self._handlers[step_id.strip()] = handler

    def get(self, step_id):
        return self._handlers.get(step_id)
