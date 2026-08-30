class MemorySummarizer:
    def __init__(self, interval=10):
        self.interval = max(1, interval)

    def summarize(self, history):
        if len(history) <= self.interval:
            return {"summary": "", "history": list(history)}
        recent = list(history[-self.interval:])
        actions = [entry.get("action", {}).get("action", "") for entry in recent]
        return {"summary": f"{len(history)} reasoning steps; recent actions: {', '.join(actions)}", "history": recent}