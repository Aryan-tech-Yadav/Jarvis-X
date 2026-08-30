import unittest

from app.architecture.architecture_engine import ArchitectureEngine
from app.autonomy.brain_layer import AutonomousBrainLayer
from app.brain.brain_pipeline import BrainPipeline
from app.governance.audit_logger import AuditLogger
from app.requirements.requirement_manager import RequirementManager
from app.risk.risk_engine import RiskEngine


class EngineeringPipelineTests(unittest.TestCase):
    def test_requirement_manager_extracts_product_features_and_questions(self):
        brief = RequirementManager().analyze("Build an Instagram-like app")
        self.assertIn("authentication", brief["features"])
        self.assertIn("uploads", brief["features"])
        self.assertTrue(brief["clarifying_questions"])

    def test_requirement_manager_rejects_non_string_goal(self):
        with self.assertRaises(ValueError):
            RequirementManager().analyze(None)

    def test_architecture_scales_product_with_realtime_feature(self):
        requirements = RequirementManager().analyze("Build a web chat app with login")
        plan = ArchitectureEngine().design(requirements)
        self.assertEqual(plan["pattern"], "event-driven modular monolith")
        self.assertEqual(plan["technology"]["cache"], "Redis")

    def test_risk_engine_flags_payments_and_authentication(self):
        requirements = RequirementManager().analyze("Build a web ecommerce app with login and checkout")
        architecture = ArchitectureEngine().design(requirements)
        report = RiskEngine().assess(requirements, architecture)
        self.assertGreaterEqual(report["score"], 40)
        self.assertIn("security", report["categories"])

    def test_pipeline_is_governed_and_traceable(self):
        brief = BrainPipeline().prepare("Build a web ecommerce app with login and checkout")
        self.assertFalse(brief["approval"]["approved"])
        self.assertEqual([item["decision"] for item in brief["audit"]], [
            "requirements_analyzed", "architecture_selected", "execution_policy_evaluated"
        ])

    def test_research_result_is_cached_without_mutation(self):
        pipeline = BrainPipeline()
        first = pipeline.prepare("Build a web app with login")
        second = pipeline.prepare("Build a web app with login")
        self.assertFalse(first["research"]["cache_hit"])
        self.assertTrue(second["research"]["cache_hit"])

    def test_audit_logger_keeps_a_copy_of_events(self):
        audit = AuditLogger()
        audit.record("selected")
        events = audit.events()
        events.clear()
        self.assertEqual(len(audit.events()), 1)

    def test_autonomous_brain_exposes_engineering_brief(self):
        brief = AutonomousBrainLayer().prepare_engineering_goal("Build a web notes app with search")
        self.assertEqual(brief["architecture"]["technology"]["backend"], "FastAPI")


if __name__ == "__main__":
    unittest.main()
