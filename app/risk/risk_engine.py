from .risk_detector import RiskDetector
from .risk_report import RiskReport
from .risk_score import RiskScore


class RiskEngine:
    def __init__(self, detector=None, scorer=None, reporter=None):
        self.detector = detector or RiskDetector()
        self.scorer = scorer or RiskScore()
        self.reporter = reporter or RiskReport()

    def assess(self, requirements, architecture):
        risks = self.detector.detect(requirements, architecture)
        score = self.scorer.calculate(risks)
        report = self.reporter.build(risks, score, self.scorer.level(score))
        report["risks"] = risks
        return report
