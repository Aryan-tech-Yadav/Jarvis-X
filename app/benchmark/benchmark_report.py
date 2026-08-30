class BenchmarkReport:
    def build(self, results, score):
        by_category = {}
        for result in results:
            by_category.setdefault(result["category"], []).append(result)
        categories = {
            name: round(sum(item["passed"] for item in values) / len(values) * 100, 2)
            for name, values in by_category.items()
        }
        return {"score": score, "passed": all(item["passed"] for item in results), "total": len(results), "passed_count": sum(item["passed"] for item in results), "categories": categories, "results": results}
