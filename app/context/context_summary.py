class ContextSummary:
    def __init__(self, threshold=100):
        self.threshold = threshold

    def summarize(self, entries):
        if len(entries) <= self.threshold:
            return {"summary": "", "entries": list(entries)}
        return {"summary": f"Summarized {len(entries)} context entries.", "entries": list(entries[-10:])}