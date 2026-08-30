class RequirementValidator:
    def validate(self, analysis):
        errors = []
        if not analysis.get("goal"):
            errors.append("A non-empty goal is required.")
        if not analysis.get("features"):
            errors.append("At least one capability must be identified before execution.")
        return {"valid": not errors, "errors": errors}
