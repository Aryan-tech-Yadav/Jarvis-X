from .intent_classifier import IntentClassifier


class IntentAnalyzer:
    def __init__(self, classifier=None):
        self.classifier = classifier or IntentClassifier()

    def analyze(self, goal, features=None):
        value = str(goal or "").casefold()
        category = "Full Stack Web Application" if any(word in value for word in ("web", "website", "ecommerce", "e-commerce")) else \
            "API Service" if "api" in value else "Software Project"
        count = len(features or ())
        complexity = "high" if count >= 6 or any(word in value for word in ("hospital", "erp", "enterprise", "saas")) else \
            "medium" if count >= 3 else "low"
        confidence = 0.95 if self.classifier.classify(goal) != "unknown" else 0.35
        return {"intent": self.classifier.classify(goal), "confidence": confidence, "category": category,
                "complexity": complexity, "estimated_modules": max(3, 3 + count * 2)}
