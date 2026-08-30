from app.strategy.strategy_evaluator import StrategyEvaluator
from app.strategy.strategy_history import StrategyHistory
from app.strategy.strategy_selector import StrategySelector


class StrategyEngine:
    """Produces, ranks, and selects alternatives before project creation."""

    def __init__(self, evaluator=None, selector=None, history=None):
        self.evaluator = evaluator or StrategyEvaluator()
        self.selector = selector or StrategySelector()
        self.history = history or StrategyHistory()

    def choose(self, goal, strategies=None):
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("Goal cannot be empty")
        candidates = strategies if strategies is not None else self.options_for(goal)
        results = [self.evaluator.evaluate(item, goal, self.history.experience(item.get("name"), goal)) for item in candidates]
        selected = self.selector.select(results)
        if selected is None:
            fallback = self.evaluator.evaluate(self._fallback(goal), goal)
            results, selected = [fallback], fallback
        return {"selected": selected.to_dict(), "alternatives": [item.to_dict() for item in self.selector.rank(results)]}

    def options_for(self, goal):
        text = goal.casefold()
        if any(word in text for word in ("desktop", "tkinter", "gui")):
            return [
                {"name": "tkinter-desktop", "description": "Native Python desktop interface", "complexity": 0.3, "dependencies": 0.1, "estimated_minutes": 35},
                {"name": "pyqt-desktop", "description": "Feature-rich desktop interface", "complexity": 0.55, "dependencies": 0.55, "estimated_minutes": 55},
            ]
        return [
            {"name": "fastapi-modular-monolith", "description": "Maintainable API-first modular application", "complexity": 0.45, "dependencies": 0.35, "estimated_minutes": 60},
            {"name": "flask-minimal", "description": "Small, fast initial web application", "complexity": 0.28, "dependencies": 0.2, "estimated_minutes": 35},
            {"name": "full-stack-web", "description": "Separate frontend and backend web interface", "complexity": 0.72, "dependencies": 0.65, "estimated_minutes": 110},
        ]

    @staticmethod
    def _fallback(goal):
        return {"name": "incremental-prototype", "description": f"Smallest safe delivery for {goal}", "complexity": 0.2, "dependencies": 0.1, "estimated_minutes": 20}
