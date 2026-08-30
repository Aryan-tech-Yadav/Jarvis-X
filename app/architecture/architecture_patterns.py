class ArchitecturePatterns:
    def choose(self, requirements):
        features = set(requirements.get("features", ()))
        constraints = set(requirements.get("constraints", ()))
        if "realtime" in features or "scale" in constraints:
            return "event-driven modular monolith"
        if len(features) >= 6:
            return "clean modular monolith"
        return "layered monolith"
