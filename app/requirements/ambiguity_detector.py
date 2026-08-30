class AmbiguityDetector:
    VAGUE_TERMS = ("like", "modern", "fast", "best", "nice", "good", "scalable", "simple")

    def detect(self, text, features=None):
        value = str(text or "").casefold()
        issues = []
        if len(value.split()) < 4:
            issues.append("The goal is too short to define scope.")
        if any(term in value.split() for term in self.VAGUE_TERMS):
            issues.append("The goal contains subjective language that needs acceptance criteria.")
        if not features:
            issues.append("No concrete user-facing capabilities were identified.")
        if not any(term in value for term in ("web", "mobile", "desktop", "api", "cli")):
            issues.append("Target platform is not specified.")
        return issues
