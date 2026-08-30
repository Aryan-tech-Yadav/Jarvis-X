from app.strategy.strategy_result import StrategyResult


class StrategyEvaluator:
    """Scores strategies using transparent heuristic inputs, not an LLM guess."""

    def evaluate(self, strategy, goal="", experience=None):
        if not isinstance(strategy, dict) or not strategy.get("name"):
            raise ValueError("Strategy must include a name")
        experience = experience or {}
        complexity = self._bounded(strategy.get("complexity", 0.5))
        dependencies = self._bounded(strategy.get("dependencies", 0.25))
        risk = self._bounded(strategy.get("risk", complexity * 0.7 + dependencies * 0.3))
        minutes = max(1, int(strategy.get("estimated_minutes", 30)))
        success_rate = self._bounded(experience.get("success_rate", 0.5))
        evidence_bonus = min(0.15, int(experience.get("attempts", 0)) * 0.03)
        score = round(100 * (0.38 * success_rate + 0.24 * (1 - risk) + 0.2 * (1 - complexity) + 0.18 * (1 - dependencies) + evidence_bonus), 2)
        confidence = round(self._bounded(0.45 + 0.45 * success_rate + evidence_bonus - 0.2 * risk), 2)
        difficulty = "low" if complexity < 0.34 else "medium" if complexity < 0.67 else "high"
        reasons = [
            f"estimated {minutes} minutes",
            f"risk score {round(risk * 100)}%",
            f"historical success {round(success_rate * 100)}%",
        ]
        return StrategyResult(
            name=strategy["name"],
            description=strategy.get("description", f"Approach for {goal}"),
            score=score,
            confidence=confidence,
            difficulty=difficulty,
            estimated_minutes=minutes,
            risk=round(risk, 2),
            reasons=tuple(reasons),
        )

    @staticmethod
    def _bounded(value):
        return max(0.0, min(1.0, float(value)))
