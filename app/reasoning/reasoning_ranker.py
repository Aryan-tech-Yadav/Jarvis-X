import time


class ReasoningRanker:
    def score(self, item, goal, now=None):
        now = time.time() if now is None else now
        overlap = len(set(str(goal).casefold().split()) & set(str(item.get("goal", "")).casefold().split()))
        age = max(0, now - float(item.get("created_at", now)))
        return overlap * 10 + float(item.get("confidence", 0.0)) * 5 + 1 / (1 + age / 86400)

    def rank(self, entries, goal, limit=5):
        return sorted(entries, key=lambda item: self.score(item, goal), reverse=True)[:max(0, limit)]
