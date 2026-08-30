class IntentClassifier:
    """Small, explainable classifier for the engineering goals Jarvis-X accepts."""

    def classify(self, goal):
        value = str(goal or "").casefold()
        if any(word in value for word in ("build", "create", "generate", "develop")):
            return "software_generation"
        if any(word in value for word in ("fix", "repair", "debug")):
            return "software_repair"
        if any(word in value for word in ("analyze", "review", "inspect")):
            return "project_analysis"
        return "unknown"
