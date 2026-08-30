class PolicyEngine:
    """Policy gate for decisions that should not enter autonomous execution."""

    def evaluate(self, requirements, risk_report):
        reasons = []
        if not requirements.get("valid"):
            reasons.extend(requirements.get("errors", ()))
        if "payments" in requirements.get("features", ()):
            reasons.append("Payment handling requires human approval before execution.")
        if risk_report.get("level") == "high":
            reasons.append("High delivery risk requires human approval before execution.")
        return {"approved": not reasons, "reasons": reasons}
