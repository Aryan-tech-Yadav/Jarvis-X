class PriorityDetector:
    HIGH_VALUE = {"authentication", "payments", "uploads", "realtime"}

    def prioritize(self, features):
        return {
            feature: "high" if feature in self.HIGH_VALUE else "medium"
            for feature in features
        }
