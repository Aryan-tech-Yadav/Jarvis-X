class ArchitectureValidator:
    REQUIRED_TECHNOLOGIES = ("backend", "database")

    def validate(self, plan):
        missing = [item for item in self.REQUIRED_TECHNOLOGIES if not plan.get("technology", {}).get(item)]
        return {"valid": not missing, "errors": ["Missing technology: " + item for item in missing]}
