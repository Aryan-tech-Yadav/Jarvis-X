class TaskDispatcher:
    def __init__(self, registry, max_retries=1):
        self.registry = registry
        self.max_retries = max(0, max_retries)

    def dispatch(self, task):
        agent = self.registry.find_best(task) if hasattr(self.registry, "find_best") else self.registry.get(task.agent)
        if agent is None:
            return {"success": False, "error": f"No agent available for task: {getattr(task, 'title', task)}"}
        for attempt in range(self.max_retries + 1):
            result = agent.run(task)
            if isinstance(result, dict) and result.get("success"):
                return result
            if attempt == self.max_retries:
                return result if isinstance(result, dict) else {"success": False, "error": "Invalid agent result"}
        return {"success": False, "error": "Dispatch failed"}