class RequirementSummary:
    def build(self, analysis):
        features = ", ".join(analysis.get("features", ())) or "no concrete features"
        constraints = ", ".join(analysis.get("constraints", ())) or "none"
        return "Goal: {goal}. Features: {features}. Constraints: {constraints}.".format(
            goal=analysis.get("goal", ""), features=features, constraints=constraints
        )
