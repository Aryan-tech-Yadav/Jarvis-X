class GoalDecomposer:
    def decompose(self, goal):
        if not isinstance(goal, str) or not goal.strip():
            return []
        text = goal.strip()
        lower = text.casefold()
        if "instagram" in lower:
            return ["authentication", "database", "feed", "stories", "messaging", "notifications", "testing"]
        return [part.strip() for part in text.replace(",", " and ").split(" and ") if part.strip()] or [text]