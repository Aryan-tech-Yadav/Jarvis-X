"""Cognitive risk facade over the existing engineering risk analyzer."""

from app.engineering.risk_analyzer import RiskAnalyzer as EngineeringRiskAnalyzer


class CognitiveRiskAnalyzer:
    def __init__(self, analyzer=None):
        self.analyzer = analyzer or EngineeringRiskAnalyzer()

    def analyze(self, requirements, architecture=None):
        payload = requirements if isinstance(requirements, dict) else requirements.to_dict()
        return self.analyzer.analyze(payload, architecture).to_dict()
