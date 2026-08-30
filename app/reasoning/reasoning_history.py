from datetime import datetime, timezone


class ReasoningHistory:
    def __init__(self):
        self.entries = []

    def record(self, goal, result, confidence=0.5):
        entry = {"goal": goal, "result": result, "confidence": float(confidence), "created_at": datetime.now(timezone.utc).timestamp()}
        self.entries.append(entry)
        return entry

    def search(self, query):
        terms = set(str(query).casefold().split())
        return [entry for entry in self.entries if terms & set(str(entry["goal"]).casefold().split())]
