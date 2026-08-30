import unittest

from app.benchmark.benchmark_case import BenchmarkCase
from app.benchmark.benchmark_runner import BenchmarkRunner
from app.brain.brain_pipeline import BrainPipeline
from app.cost.cost_analyzer import CostAnalyzer
from app.cost.resource_cost import ResourceCost
from app.cost.time_cost import TimeCost
from app.cost.token_cost import TokenCost
from app.optimizer.dependency_optimizer import DependencyOptimizer
from app.optimizer.execution_optimizer import ExecutionOptimizer
from app.optimizer.step_merger import StepMerger
from app.optimizer.step_splitter import StepSplitter
from app.requirements.requirement_manager import RequirementManager
from app.simulation.dependency_simulator import DependencySimulator
from app.simulation.project_simulator import ProjectSimulator
from app.simulation.risk_simulator import RiskSimulator
from app.strategy.strategy_engine import StrategyEngine
from app.strategy.strategy_evaluator import StrategyEvaluator
from app.strategy.strategy_history import StrategyHistory
from app.strategy.strategy_selector import StrategySelector


class StrategyEngineTests(unittest.TestCase):
    def test_strategy_engine_supplies_ranked_default_options(self):
        result = StrategyEngine().choose("Build a chat application")
        self.assertGreaterEqual(len(result["alternatives"]), 2)
        self.assertEqual(result["selected"], result["alternatives"][0])

    def test_strategy_engine_selects_desktop_option_for_gui_goal(self):
        result = StrategyEngine().choose("Build a desktop GUI calculator")
        self.assertEqual(result["selected"]["name"], "tkinter-desktop")

    def test_strategy_engine_rejects_empty_goal(self):
        with self.assertRaises(ValueError):
            StrategyEngine().choose(" ")

    def test_evaluator_includes_estimates_and_confidence(self):
        result = StrategyEvaluator().evaluate({"name": "safe", "complexity": 0.2, "dependencies": 0.1, "estimated_minutes": 10})
        self.assertEqual(result.difficulty, "low")
        self.assertGreater(result.confidence, 0)

    def test_evaluator_rejects_unnamed_strategy(self):
        with self.assertRaises(ValueError):
            StrategyEvaluator().evaluate({})

    def test_history_prefers_successful_prior_experience(self):
        history = StrategyHistory()
        history.record("Build a web API", "fastapi", True)
        history.record("Build another API", "fastapi", True)
        history.record("Build API", "flask", False)
        result = StrategyEngine(history=history).choose("Build API", [
            {"name": "fastapi", "complexity": 0.5, "dependencies": 0.4},
            {"name": "flask", "complexity": 0.3, "dependencies": 0.2},
        ])
        self.assertEqual(result["selected"]["name"], "fastapi")

    def test_history_returns_neutral_unknown_experience(self):
        self.assertEqual(StrategyHistory().experience("unknown"), {"attempts": 0, "success_rate": 0.5})

    def test_selector_breaks_score_ties_by_lower_risk(self):
        evaluator = StrategyEvaluator()
        first = evaluator.evaluate({"name": "high-risk", "risk": 0.7})
        second = evaluator.evaluate({"name": "low-risk", "risk": 0.2})
        first = first.__class__(**{**first.__dict__, "score": 50})
        second = second.__class__(**{**second.__dict__, "score": 50})
        self.assertEqual(StrategySelector().select([first, second]).name, "low-risk")

    def test_empty_options_use_incremental_fallback(self):
        self.assertEqual(StrategyEngine().choose("Build tool", []) ["selected"]["name"], "incremental-prototype")


class SimulationTests(unittest.TestCase):
    def setUp(self):
        self.requirements = RequirementManager().analyze("Build an ecommerce web app with login, image upload, and checkout")

    def test_dependency_simulation_infers_feature_dependencies(self):
        dependencies = DependencySimulator().estimate(self.requirements, {"technology": {"backend": "FastAPI", "database": "PostgreSQL"}})
        self.assertIn("fastapi", dependencies)
        self.assertIn("python-jose", dependencies)
        self.assertIn("stripe", dependencies)

    def test_risk_simulation_flags_auth_uploads_and_payments(self):
        risks = RiskSimulator().estimate(self.requirements)
        self.assertGreaterEqual(len(risks), 3)

    def test_project_simulation_estimates_files_time_and_confidence(self):
        result = ProjectSimulator().simulate(self.requirements, {"modules": {"api": []}}, {"estimated_minutes": 40})
        self.assertGreater(result["estimated_files"], 5)
        self.assertGreater(result["estimated_minutes"], 40)
        self.assertLessEqual(result["confidence"], 0.9)

    def test_simulator_reports_missing_requirement_questions(self):
        result = ProjectSimulator().simulate(RequirementManager().analyze("Build app"))
        self.assertTrue(result["missing_requirements"])

    def test_simulator_never_estimates_less_than_three_files(self):
        result = ProjectSimulator().simulate({"features": [], "clarifying_questions": [], "constraints": ["small"]})
        self.assertGreaterEqual(result["estimated_files"], 3)


class CostAnalyzerTests(unittest.TestCase):
    def test_token_cost_calculates_calls_tokens_and_price(self):
        result = TokenCost().estimate(2, 1500, 0.5)
        self.assertEqual(result["tokens"], 3000)
        self.assertEqual(result["estimated_cost"], 1.5)

    def test_time_cost_uses_hourly_rate(self):
        self.assertEqual(TimeCost().estimate(30, 40)["estimated_cost"], 20.0)

    def test_resource_cost_handles_optional_measurements(self):
        result = ResourceCost().estimate(files=10, dependencies=2, memory_mb=512, cpu_seconds=1800)
        self.assertGreaterEqual(result["resource_units"], 3)

    def test_cost_analyzer_returns_optimization_suggestions(self):
        result = CostAnalyzer().analyze({"estimated_files": 30, "estimated_minutes": 120, "dependencies": ["a", "b", "c", "d"]}, ai_calls=7)
        self.assertEqual(len(result["optimizations"]), 3)

    def test_cost_analyzer_returns_lean_suggestion_for_small_project(self):
        result = CostAnalyzer().analyze({"estimated_files": 3, "estimated_minutes": 5, "dependencies": []})
        self.assertEqual(result["optimizations"], ["Current execution estimate is already lean."])


class ExecutionOptimizerTests(unittest.TestCase):
    def test_merger_combines_validation_and_test_steps(self):
        result = StepMerger().merge(["design", "validate", "test", "document"])
        self.assertEqual(result[1]["name"], "validate + test")

    def test_splitter_splits_large_steps_into_chained_parts(self):
        result = StepSplitter().split([{"name": "implement", "estimated_files": 25}], max_files=10)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[1]["dependencies"], ["implement (1/3)"])

    def test_splitter_rewrites_following_dependency_to_final_part(self):
        result = StepSplitter().split([{"name": "implement", "estimated_files": 25}, {"name": "test", "dependencies": ["implement"]}], max_files=10)
        self.assertEqual(result[-1]["dependencies"], ["implement (3/3)"])

    def test_dependency_optimizer_orders_dependencies(self):
        steps = [{"name": "test", "dependencies": ["code"]}, {"name": "code", "dependencies": ["design"]}, {"name": "design"}]
        self.assertEqual([item["name"] for item in DependencyOptimizer().order(steps)], ["design", "code", "test"])

    def test_dependency_optimizer_rejects_cycles(self):
        with self.assertRaises(ValueError):
            DependencyOptimizer().order([{"name": "a", "dependencies": ["b"]}, {"name": "b", "dependencies": ["a"]}])

    def test_execution_optimizer_merges_validation_and_exposes_parallel_group(self):
        result = ExecutionOptimizer().optimize([{"name": "design"}, {"name": "implement", "dependencies": ["design"]}, {"name": "validate", "dependencies": ["implement"], "parallelizable": True}, {"name": "test", "dependencies": ["implement"], "parallelizable": True}])
        self.assertEqual(result["steps"][-1]["name"], "validate + test")
        self.assertEqual(result["parallel_groups"][-1][0]["name"], "validate + test")


class BenchmarkTests(unittest.TestCase):
    def test_benchmark_scores_passing_cases(self):
        cases = [BenchmarkCase("plan", True, category="planning"), BenchmarkCase("test", True, category="quality")]
        result = BenchmarkRunner().run(cases, {"plan": True, "test": True})
        self.assertEqual(result["score"], 100.0)
        self.assertTrue(result["passed"])

    def test_benchmark_supports_callable_expectations(self):
        result = BenchmarkRunner().run([BenchmarkCase("risk", lambda value: value < 30)], {"risk": 20})
        self.assertTrue(result["passed"])

    def test_benchmark_applies_weighting(self):
        result = BenchmarkRunner().run([BenchmarkCase("important", True, weight=3), BenchmarkCase("minor", True, weight=1)], {"important": False, "minor": True})
        self.assertEqual(result["score"], 25.0)

    def test_empty_benchmark_is_zero_and_vacuously_passing(self):
        result = BenchmarkRunner().run([], {})
        self.assertEqual(result["score"], 0.0)
        self.assertTrue(result["passed"])


class SprintIntegrationTests(unittest.TestCase):
    def test_brain_pipeline_enriches_governed_brief_with_sprint_two_outputs(self):
        result = BrainPipeline().prepare("Build a web notes app with login and search")
        self.assertIn("strategy", result)
        self.assertIn("simulation", result)
        self.assertIn("cost", result)
        self.assertIn("execution", result)
        self.assertEqual(result["audit"][-1]["decision"], "execution_policy_evaluated")

    def test_pipeline_execution_plan_has_a_validated_combined_step(self):
        result = BrainPipeline().prepare("Build a web notes app")
        self.assertTrue(any("validate" in item["name"] and "test" in item["name"] for item in result["execution"]["steps"]))


if __name__ == "__main__":
    unittest.main()
