from app.benchmark.benchmark_report import BenchmarkReport
from app.benchmark.benchmark_score import BenchmarkScore


class BenchmarkRunner:
    def __init__(self, scorer=None, reporter=None):
        self.scorer = scorer or BenchmarkScore()
        self.reporter = reporter or BenchmarkReport()

    def run(self, cases, subject):
        results = []
        for case in cases:
            actual = subject(case) if callable(subject) else subject.get(case.name) if isinstance(subject, dict) else None
            results.append(case.evaluate(actual))
        return self.reporter.build(results, self.scorer.calculate(results))
