class ReleaseQualityGate:
    """Evaluates reliable preflight behavior, not authorization policy outcomes.

    A policy block is the desired result for high-risk or regulated work. It
    must therefore remain visible in reports without making the benchmark's
    planning/validation quality gate fail.
    """

    def __init__(self, minimum_preflight_rate=0.85, required_projects=20):
        self.minimum_preflight_rate = self._rate(minimum_preflight_rate)
        self.required_projects = max(1, int(required_projects))

    def evaluate(self, report):
        total = int(report.get("total", 0))
        preflight_rate = float(report.get("preflight_rate", 0.0))
        checks = {
            "complete_catalog": total >= self.required_projects,
            "preflight_reliability": preflight_rate >= self.minimum_preflight_rate,
        }
        return {
            "passed": all(checks.values()),
            "checks": checks,
            "thresholds": {
                "minimum_preflight_rate": self.minimum_preflight_rate,
                "required_projects": self.required_projects,
            },
        }

    @staticmethod
    def _rate(value):
        value = float(value)
        return value / 100 if value > 1 else max(0.0, min(1.0, value))
