class RiskDetector:
    WEIGHTS = {
        "payments": ("security", 25), "authentication": ("security", 15),
        "uploads": ("security", 10), "realtime": ("performance", 15),
        "notifications": ("dependency", 8), "admin": ("security", 8),
    }

    def detect(self, requirements, architecture):
        risks = []
        for feature in requirements.get("features", ()):
            if feature in self.WEIGHTS:
                category, score = self.WEIGHTS[feature]
                risks.append({"category": category, "source": feature, "score": score})
        if requirements.get("ambiguities"):
            risks.append({"category": "timeline", "source": "ambiguous requirements", "score": 12})
        risks.extend({"category": "scalability", "source": warning, "score": 8} for warning in architecture.get("scalability_warnings", ()))
        return risks
