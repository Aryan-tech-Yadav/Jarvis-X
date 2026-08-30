class ReflectionMetrics:
    def __init__(self):
        self.reports = []

    def record(self, report):
        self.reports.append(report.to_dict() if hasattr(report, "to_dict") else dict(report))

    def averages(self):
        if not self.reports:
            return {}
        areas = self.reports[0].get("scores", {})
        return {area: sum(report["scores"].get(area, 0) for report in self.reports) / len(self.reports) for area in areas}
