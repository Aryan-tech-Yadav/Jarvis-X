from app.diagnostics.health_checker import HealthChecker


class SystemReport:
    def __init__(self, health_checker=None):
        self.health_checker = health_checker or HealthChecker()

    def generate(self):
        result = self.health_checker.check()
        lines = [f"{'OK' if value else 'FAIL'} {name}" for name, value in result["checks"].items()]
        return {**result, "text": "\n".join(lines)}