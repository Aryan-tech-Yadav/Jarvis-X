import unittest

from app.agents.agent_registry import AgentRegistry
from app.brain.brain_pipeline import BrainPipeline
from app.core.context import JarvisContext
from app.core.interfaces import LifecycleComponent
from app.core.registry import ModuleRegistry
from app.core.results import ExecutionResult
from app.orchestrator.agent_orchestrator import AgentOrchestrator
from app.orchestrator.shared_context import SharedContext


class CoreResultTests(unittest.TestCase):
    def test_completed_result_has_the_standard_response_fields(self):
        result = ExecutionResult.completed({"plan": "safe"}, metrics={"calls": 1}, artifacts=["brief.json"])
        payload = result.to_dict()
        self.assertEqual(set(payload), {"success", "status", "message", "data", "metrics", "warnings", "errors", "artifacts", "duration"})
        self.assertTrue(payload["success"])
        self.assertEqual(payload["status"], "completed")

    def test_failed_result_normalizes_error_text(self):
        result = ExecutionResult.failed("validation failed")
        self.assertFalse(result.success)
        self.assertEqual(result.errors, ["validation failed"])

    def test_inconsistent_success_and_failed_status_is_rejected(self):
        with self.assertRaises(ValueError):
            ExecutionResult(True, "failed")

    def test_legacy_success_mapping_keeps_full_data(self):
        source = {"success": True, "output": "done", "context": {"goal": "Build app"}}
        result = ExecutionResult.from_legacy(source)
        self.assertTrue(result.success)
        self.assertIs(result.data, source)

    def test_legacy_unmarked_mapping_is_treated_as_successful_data(self):
        result = ExecutionResult.from_legacy({"architecture": "modular"})
        self.assertTrue(result.success)
        self.assertEqual(result.data["architecture"], "modular")

    def test_legacy_tuple_failure_is_normalized(self):
        result = ExecutionResult.from_legacy((False, "missing project"))
        self.assertFalse(result.success)
        self.assertIn("missing project", result.errors)

    def test_timed_converts_exceptions_to_failed_results(self):
        result = ExecutionResult.timed(lambda: (_ for _ in ()).throw(RuntimeError("boom")))
        self.assertFalse(result.success)
        self.assertGreaterEqual(result.duration, 0)


class CoreContextTests(unittest.TestCase):
    def test_context_tracks_steps_events_and_metrics(self):
        context = JarvisContext("Build API")
        step = context.start_step("planning")
        context.finish_step(step, message="plan created")
        context.add_metric("llm_calls", 2)
        context.add_event("PLAN_CREATED", {"steps": 3})
        self.assertEqual(context.current_step, "planning")
        self.assertEqual(context.metrics["llm_calls"], 2)
        self.assertEqual(context.events[0]["type"], "PLAN_CREATED")
        self.assertEqual(context.timeline[0]["status"], "completed")

    def test_context_rejects_empty_goal(self):
        with self.assertRaises(ValueError):
            JarvisContext(" ")

    def test_shared_context_inherits_shared_fields_and_keeps_base_path(self):
        context = SharedContext(goal="Build API", base_path="workspace/api")
        self.assertEqual(context.project_path, "workspace/api")
        context.add_metric("repairs")
        payload = context.as_dict()
        self.assertEqual(payload["base_path"], "workspace/api")
        self.assertEqual(payload["metrics"]["repairs"], 1)


class RegistryAndLifecycleTests(unittest.TestCase):
    def test_registry_registers_gets_and_requires_modules(self):
        registry = ModuleRegistry()
        component = object()
        registry.register("planner", component)
        self.assertIs(registry.get("planner"), component)
        self.assertIs(registry.require("planner"), component)
        self.assertEqual(registry.names(), ("planner",))

    def test_registry_rejects_blank_name_and_unknown_requirement(self):
        registry = ModuleRegistry()
        with self.assertRaises(ValueError):
            registry.register("", object())
        with self.assertRaises(KeyError):
            registry.require("missing")

    def test_lifecycle_component_has_safe_default_hooks(self):
        component = LifecycleComponent()
        self.assertTrue(component.initialize())
        self.assertTrue(component.validate())
        self.assertTrue(component.cleanup())
        self.assertTrue(component.shutdown())


class ResultBoundaryIntegrationTests(unittest.TestCase):
    def test_engineering_pipeline_provides_standard_result(self):
        result = BrainPipeline().prepare_result("Build a web notes app with login")
        self.assertTrue(result.success)
        self.assertEqual(result.status, "completed")
        self.assertIn("architecture", result.data)
        self.assertIn("risk_score", result.metrics)

    def test_engineering_pipeline_normalizes_invalid_input(self):
        result = BrainPipeline().prepare_result(None)
        self.assertFalse(result.success)
        self.assertEqual(result.status, "failed")

    def test_orchestrator_provides_standard_result_without_changing_legacy_flow(self):
        class Agent:
            def execute(self, context):
                return {"success": True, "output": "done"}

        registry = AgentRegistry()
        for name in ("planner", "coder", "tester", "reviewer", "documentation"):
            registry.register(name, Agent())
        result = AgentOrchestrator(registry=registry).run_result("Build API")
        self.assertTrue(result.success)
        self.assertEqual(result.metrics["agent_steps"], 5)
        self.assertEqual(result.status, "completed")


if __name__ == "__main__":
    unittest.main()
