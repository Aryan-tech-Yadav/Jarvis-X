class RiskSimulator:
    def estimate(self, requirements, architecture=None):
        features = set(requirements.get("features", ()))
        risks = []
        if "authentication" in features:
            risks.append("authentication design and credential storage")
        if "uploads" in features:
            risks.append("file upload validation and storage")
        if "payments" in features:
            risks.append("payment compliance and webhook verification")
        if len(features) >= 6:
            risks.append("large scope requires incremental delivery")
        if not requirements.get("constraints"):
            risks.append("missing scale, budget, or privacy constraints")
        return risks
