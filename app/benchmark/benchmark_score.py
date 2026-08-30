class BenchmarkScore:
    def calculate(self, results):
        total = sum(item["weight"] for item in results)
        if total == 0:
            return 0.0
        return round(sum(item["weight"] for item in results if item["passed"]) / total * 100, 2)
