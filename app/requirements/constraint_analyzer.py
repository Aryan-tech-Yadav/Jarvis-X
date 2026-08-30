class ConstraintAnalyzer:
    def analyze(self, text):
        value = str(text or "").casefold()
        constraints = []
        for name, keywords in {
            "offline": ("offline", "local only"),
            "privacy": ("private", "privacy", "gdpr"),
            "budget": ("budget", "cheap", "free"),
            "deadline": ("today", "tomorrow", "deadline", "urgent"),
            "scale": ("million", "scale", "high traffic"),
        }.items():
            if any(keyword in value for keyword in keywords):
                constraints.append(name)
        return constraints
