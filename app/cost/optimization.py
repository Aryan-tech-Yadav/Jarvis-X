class Optimization:
    def suggest(self, simulation, token_cost):
        suggestions = []
        if token_cost["ai_calls"] > 5:
            suggestions.append("Reuse planning and design outputs to reduce AI calls.")
        if simulation.get("estimated_files", 0) > 20:
            suggestions.append("Deliver the project in independently validated milestones.")
        if len(simulation.get("dependencies", ())) > 3:
            suggestions.append("Pin and audit dependencies before generation.")
        return suggestions or ["Current execution estimate is already lean."]
