"""Pre-execution cognitive pipeline used by the engineering runtime."""

from app.reasoning.clarification_engine import ClarificationEngine
from app.reasoning.goal_analyzer import GoalAnalyzer
from app.risk.risk_analyzer import CognitiveRiskAnalyzer


class CognitivePipeline:
    def __init__(self, goal_analyzer=None, clarification=None, risk_analyzer=None):
        self.goal_analyzer = goal_analyzer or GoalAnalyzer()
        self.clarification = clarification or ClarificationEngine()
        self.risk_analyzer = risk_analyzer or CognitiveRiskAnalyzer()

    def assess(self, goal: str):
        understanding = self.goal_analyzer.analyze(goal)
        clarification = self.clarification.analyze(goal)
        risk = self.risk_analyzer.analyze(understanding["requirements"])
        return {
            "understanding": understanding,
            "clarification": clarification,
            "risk": risk,
            "ready_for_execution": not clarification["questions"],
        }
