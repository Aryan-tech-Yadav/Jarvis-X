from app.reasoning.decision import Decision


class DecisionEngine:
    def choose(self, decisions):
        values = [item if isinstance(item, Decision) else Decision(**item) for item in decisions]
        return max(values, key=lambda item: (item.confidence, item.priority == "HIGH"), default=None)

    def explain(self, decision):
        """Return a serializable decision with its confidence and rationale."""
        value = decision if isinstance(decision, Decision) else Decision(**decision)
        return value.to_dict()