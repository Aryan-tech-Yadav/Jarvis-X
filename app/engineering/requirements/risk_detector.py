"""Requirement risk detection facade."""

from app.engineering.risk_analyzer import RiskAnalyzer


class RiskDetector:
    def __init__(self, analyzer=None):
        self.analyzer = analyzer or RiskAnalyzer()

    def detect(self, requirements) -> dict:
        return self.analyzer.analyze(requirements.to_dict()).to_dict()

