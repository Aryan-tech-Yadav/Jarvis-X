class DashboardMetrics:
    def calculate(self, data):
        result = dict(data)
        attempts = result["successes"] + result["failures"]
        result["success_rate"] = result["successes"] / attempts if attempts else 0.0
        result["repair_rate"] = result["repairs"] / result["projects"] if result["projects"] else 0.0
        return result
