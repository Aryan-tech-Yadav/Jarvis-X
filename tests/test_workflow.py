import unittest

from app.brain.brain_pipeline import BrainPipeline
from app.events.event_bus import EventBus
from app.workflow.exceptions import WorkflowValidationError
from app.workflow.models import Workflow, WorkflowStep
from app.workflow.workflow_builder import WorkflowBuilder
from app.workflow.workflow_engine import WorkflowEngine
from app.workflow.workflow_manager import WorkflowManager
from app.workflow.workflow_registry import WorkflowRegistry
from app.workflow.workflow_validator import WorkflowValidator


class WorkflowTests(unittest.TestCase):
    def test_builder_selects_research_repair_and_deployment_for_complex_goal(self):
        workflow = WorkflowBuilder().build(
            "Build and deploy an ecommerce application",
            {"features": ["authentication", "payments", "uploads"], "ambiguities": []},
            {"score": 50},
            {"risks": ["security"]},
        )

        self.assertEqual(workflow.status.value, "ready")
        self.assertEqual([step.step_id for step in workflow.steps], [
            "requirements", "research", "architecture", "planning", "execution",
            "validation", "testing", "repair", "documentation", "deployment",
        ])
        self.assertEqual(workflow.step("architecture").depends_on, ("requirements", "research"))

    def test_builder_omits_optional_stages_for_small_low_risk_goal(self):
        workflow = WorkflowBuilder().build("Build a calculator", {"features": []}, {"score": 0}, {"risks": []})

        self.assertNotIn("research", [step.step_id for step in workflow.steps])
        self.assertNotIn("repair", [step.step_id for step in workflow.steps])
        self.assertNotIn("deployment", [step.step_id for step in workflow.steps])

    def test_validator_rejects_dependency_cycles(self):
        workflow = Workflow("goal", [WorkflowStep("one", "One", ("two",)), WorkflowStep("two", "Two", ("one",))])

        with self.assertRaises(WorkflowValidationError):
            WorkflowValidator().validate(workflow)

    def test_execution_honors_dependencies_signals_and_event_history(self):
        bus = EventBus()
        calls = []

        def handler(step, context):
            calls.append(step.step_id)
            signals = {"repair_required": True} if step.step_id == "validation" else {}
            return {"success": True, "signals": signals}

        registry = WorkflowRegistry()
        for name in ("requirements", "research", "architecture", "planning", "execution", "validation", "testing", "repair", "documentation"):
            registry.register(name, handler)
        workflow = WorkflowBuilder().build("Build API", {"features": []}, {"score": 40}, {"risks": []})
        result = WorkflowEngine(manager=WorkflowManager(registry, bus)).run(workflow)

        self.assertTrue(result["success"])
        self.assertLess(calls.index("validation"), calls.index("repair"))
        self.assertLess(calls.index("testing"), calls.index("documentation"))
        self.assertTrue(any(event.event_type == "WORKFLOW_STEP_COMPLETED" for event in bus.history))

    def test_required_missing_handler_fails_without_running_dependents(self):
        registry = WorkflowRegistry({"requirements": lambda step, context: {"success": True}})
        workflow = WorkflowBuilder().build("Build tool", {"features": []}, {"score": 0}, {"risks": []})
        result = WorkflowEngine(manager=WorkflowManager(registry)).run(workflow)

        self.assertFalse(result["success"])
        self.assertEqual(result["workflow"]["steps"][1]["status"], "failed")
        self.assertEqual(result["workflow"]["steps"][2]["status"], "pending")

    def test_brain_pipeline_exposes_advisory_workflow(self):
        brief = BrainPipeline().prepare("Build a web application with login and payments")

        self.assertEqual(brief["workflow"]["goal"], brief["goal"])
        self.assertEqual(brief["workflow"]["status"], "ready")


if __name__ == "__main__":
    unittest.main()
