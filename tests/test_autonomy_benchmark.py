import unittest

from app.benchmark import AutonomyBenchmarkCatalog, AutonomyBenchmarkRunner


class TestAutonomyBenchmark(unittest.TestCase):
    def test_catalog_contains_ten_research_benchmarks(self):
        catalog = AutonomyBenchmarkCatalog()
        self.assertEqual(len(catalog.list()), 10)
        self.assertIsNotNone(catalog.get("production-bug"))

    def test_runner_reports_success_and_automation(self):
        def handler(benchmark):
            return {
                "success": True,
                "manual_intervention": 0.1,
                "criteria": {criterion: True for criterion in benchmark.criteria},
            }

        report = AutonomyBenchmarkRunner().run(handler, tier="basic")
        self.assertEqual(report["successful"], 1)
        self.assertEqual(report["automation_rate"], 0.9)
        self.assertTrue(report["results"][0]["success"])

    def test_runner_rejects_non_mapping_handler_result(self):
        with self.assertRaises(TypeError):
            AutonomyBenchmarkRunner().run(lambda benchmark: None, tier="basic")


if __name__ == "__main__":
    unittest.main()
