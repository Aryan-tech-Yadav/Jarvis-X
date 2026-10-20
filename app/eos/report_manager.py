"""Public EOS report manager."""

from app.reports.execution_report import ExecutionReport


class ReportManager:
    """Create and persist execution reports."""

    def __init__(self, directory: str = ".jarvis/eos-reports"):
        self.directory = directory

    def create(self, goal: str) -> ExecutionReport:
        return ExecutionReport(goal)

    def save(self, report: ExecutionReport):
        return report.save(self.directory)


__all__ = ["ReportManager", "ExecutionReport"]
