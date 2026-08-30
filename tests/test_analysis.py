import unittest

from app.analysis.analysis_engine import AnalysisEngine
from app.analysis.architecture.api_designer import APIDesigner
from app.analysis.architecture.database_designer import DatabaseDesigner
from app.analysis.architecture.tech_stack_selector import TechStackSelector
from app.analysis.intent.intent_analyzer import IntentAnalyzer
from app.analysis.models.requirement_model import RequirementModel
from app.analysis.requirements.clarifier import RequirementClarifier
from app.analysis.requirements.extractor import RequirementExtractor
from app.brain.brain_pipeline import BrainPipeline


class AnalysisEngineTests(unittest.TestCase):
    def test_intent_identifies_full_stack_generation_and_complexity(self):
        result = IntentAnalyzer().analyze("Build an ecommerce website", ["authentication"] * 6)
        self.assertEqual(result["intent"], "software_generation")
        self.assertEqual(result["category"], "Full Stack Web Application")
        self.assertEqual(result["complexity"], "high")

    def test_requirements_infer_hospital_domain_and_non_functional_needs(self):
        result = RequirementExtractor().extract("Build a hospital system with Docker deployment")
        self.assertIn("appointments", result.functional)
        self.assertIn("billing", result.functional)
        self.assertIn("deployment", result.non_functional)

    def test_clarifier_requests_unspecified_roles_and_delivery_decisions(self):
        requirements = RequirementModel(functional=["appointments"], non_functional=[])
        result = RequirementClarifier().clarify("Build hospital system", requirements)
        self.assertIn("Which user roles and permissions are required?", result.questions)
        self.assertTrue(result.missing)

    def test_stack_comparison_selects_the_highest_scored_candidate(self):
        requirements = RequirementModel(functional=["authentication", "search", "admin"])
        selected = TechStackSelector().select(requirements, {"category": "Full Stack Web Application", "complexity": "medium"})
        self.assertEqual(selected["selected"], selected["candidates"][0])
        self.assertEqual(selected["selected"]["stack"], "FastAPI + React")

    def test_database_and_api_design_cover_ecommerce_workflows(self):
        requirements = RequirementModel(functional=["authentication", "payments", "search"])
        database = DatabaseDesigner().design("Build an ecommerce web application", requirements)
        api = APIDesigner().design(requirements)
        self.assertIn("orders", database["entities"])
        self.assertIn({"method": "POST", "path": "/checkout", "purpose": "payments"}, api["endpoints"])

    def test_analysis_engine_returns_complete_planning_package(self):
        report = AnalysisEngine().analyze("Build a hospital web system for 5 hospitals with appointment scheduling and billing")
        package = report["planning_package"]
        self.assertEqual(set(package), {"intent", "requirements", "architecture", "database", "api", "tech_stack", "constraints", "risk", "complexity", "cost", "clarifying_questions"})
        self.assertIn("appointments", package["requirements"]["functional"])
        self.assertIn("appointments", package["database"]["entities"])
        self.assertGreater(package["complexity"]["estimated_endpoints"], 0)

    def test_brain_pipeline_exposes_analysis_and_planning_package(self):
        brief = BrainPipeline().prepare("Build a web notes app with login and search")
        self.assertIn("analysis", brief)
        self.assertEqual(brief["planning_package"], brief["analysis"]["planning_package"])
        self.assertEqual(brief["planning_package"]["risk"], brief["risk"])


if __name__ == "__main__":
    unittest.main()
