import json
import os
import tempfile
import unittest

from app.benchmark.benchmark_history import BenchmarkHistory
from app.benchmark.golden_benchmark_runner import GoldenBenchmarkRunner
from app.benchmark.golden_project import GoldenProject
from app.benchmark.golden_suite import GoldenBenchmarkSuite
from app.benchmark.release_quality_gate import ReleaseQualityGate
from app.autonomy.brain_layer import AutonomousBrainLayer


class GoldenBenchmarkSuiteTests(unittest.TestCase):
    def test_suite_contains_twenty_named_projects(self):
        projects = GoldenBenchmarkSuite().projects()
        self.assertEqual(len(projects), 20)
        self.assertEqual(len({project.identifier for project in projects}), 20)

    def test_suite_is_grouped_across_four_tiers(self):
        tiers = GoldenBenchmarkSuite().tiers()
        self.assertEqual({name: len(items) for name, items in tiers.items()}, {
            "basic": 4, "intermediate": 6, "advanced": 5, "expert": 5,
        })

    def test_suite_can_lookup_project(self):
        project = GoldenBenchmarkSuite().get("ecommerce")
        self.assertEqual(project.title, "E-commerce")
        self.assertTrue(project.requires_approval)

    def test_suite_returns_none_for_unknown_project(self):
        self.assertIsNone(GoldenBenchmarkSuite().get("unknown"))

    def test_project_serializes_without_mutating_feature_tuple(self):
        project = GoldenProject("demo", "Demo", "Build demo", "basic", ("core",))
        payload = project.to_dict()
        payload["required_features"].append("changed")
        self.assertEqual(project.required_features, ("core",))


class GoldenBenchmarkRunnerTests(unittest.TestCase):
    def test_preflight_runs_the_complete_catalog(self):
        report = GoldenBenchmarkRunner().run()
        self.assertEqual(report["total"], 20)
        self.assertEqual(report["preflight_passed"], 20)
        self.assertEqual(report["tiers"]["basic"]["total"], 4)

    def test_financial_projects_are_safely_marked_for_approval(self):
        report = GoldenBenchmarkRunner().run()
        ecommerce = next(item for item in report["results"] if item["project"]["id"] == "ecommerce")
        self.assertEqual(ecommerce["status"], "needs_approval")
        self.assertTrue(ecommerce["preflight_passed"])

    def test_non_financial_projects_are_ready_after_preflight(self):
        report = GoldenBenchmarkRunner().run(tier="basic")
        self.assertTrue(all(item["status"] == "ready" for item in report["results"]))

    def test_tier_filter_runs_only_requested_projects(self):
        report = GoldenBenchmarkRunner().run(tier="expert")
        self.assertEqual(report["total"], 5)
        self.assertEqual(set(report["tiers"]), {"expert"})

    def test_execution_requires_an_explicit_handler(self):
        with self.assertRaises(ValueError):
            GoldenBenchmarkRunner().run(execute=True)

    def test_execution_handler_only_receives_ready_projects(self):
        called = []

        def execute(project, brief):
            called.append(project.identifier)
            return {"success": True, "project_path": "/safe/project"}

        report = GoldenBenchmarkRunner().run(tier="basic", execute=True, execution_handler=execute)
        self.assertEqual(len(called), 4)
        self.assertTrue(all("execution" in item for item in report["results"]))

    def test_failed_execution_is_reported_without_hiding_preflight_success(self):
        report = GoldenBenchmarkRunner().run(
            tier="basic", execute=True,
            execution_handler=lambda project, brief: {"success": project.identifier != "calculator"},
        )
        calculator = report["results"][0]
        self.assertTrue(calculator["preflight_passed"])
        self.assertEqual(calculator["status"], "execution_failed")

    def test_runner_records_report_in_history(self):
        history = BenchmarkHistory()
        runner = GoldenBenchmarkRunner(history=history)
        runner.run(tier="basic")
        self.assertEqual(history.latest()["report"]["total"], 4)

    def test_runner_uses_a_fresh_pipeline_per_project(self):
        pipelines = []

        class Pipeline:
            def prepare(self, goal):
                return {
                    "requirements": {"valid": True, "features": ["core"], "goal": goal},
                    "architecture": {"valid": True},
                    "strategy": {"selected": {"name": "safe"}},
                    "simulation": {"estimated_files": 1, "estimated_minutes": 1},
                    "execution": {"steps": [{"name": "validate + test"}]},
                    "risk": {"score": 0},
                    "approval": {"approved": True, "reasons": []},
                }

        def factory():
            item = Pipeline()
            pipelines.append(item)
            return item

        suite = type("Suite", (), {"projects": lambda self, tier=None: [GoldenProject("one", "One", "Build core", "basic", ("core",))]})()
        report = GoldenBenchmarkRunner(suite=suite, pipeline_factory=factory).run()
        self.assertTrue(report["preflight_passed"])
        self.assertEqual(len(pipelines), 1)


class BenchmarkHistoryTests(unittest.TestCase):
    def test_history_persists_and_restores_json_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "benchmark-history.json")
            BenchmarkHistory(path).record({"score": 75})
            self.assertEqual(BenchmarkHistory(path).latest()["report"]["score"], 75)

    def test_history_recovers_from_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "benchmark-history.json")
            with open(path, "w", encoding="utf-8") as file:
                file.write("not json")
            self.assertEqual(BenchmarkHistory(path).runs(), [])

    def test_history_returns_copies(self):
        history = BenchmarkHistory()
        history.record({"results": []})
        history.runs()[0]["report"]["results"].append("mutated")
        self.assertEqual(history.runs()[0]["report"]["results"], [])


class ReleaseQualityGateTests(unittest.TestCase):
    def test_quality_gate_accepts_complete_reliable_report(self):
        result = ReleaseQualityGate(required_projects=2).evaluate({"total": 2, "preflight_rate": 1, "ready_rate": 0})
        self.assertTrue(result["passed"])

    def test_quality_gate_rejects_incomplete_catalog(self):
        result = ReleaseQualityGate(required_projects=20).evaluate({"total": 19, "preflight_rate": 1, "ready_rate": 1})
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["complete_catalog"])

    def test_quality_gate_accepts_percentage_thresholds(self):
        gate = ReleaseQualityGate(minimum_preflight_rate=85, required_projects=1)
        self.assertTrue(gate.evaluate({"total": 1, "preflight_rate": 0.85, "ready_rate": 0})["passed"])

    def test_quality_gate_rejects_low_preflight_reliability(self):
        result = ReleaseQualityGate(required_projects=1).evaluate({"total": 1, "preflight_rate": 0.84})
        self.assertFalse(result["passed"])


class GoldenBenchmarkIntegrationTests(unittest.TestCase):
    def test_autonomous_brain_exposes_non_destructive_golden_benchmarks(self):
        report = AutonomousBrainLayer().run_golden_benchmarks(tier="basic")
        self.assertEqual(report["mode"], "preflight")
        self.assertEqual(report["total"], 4)


if __name__ == "__main__":
    unittest.main()
