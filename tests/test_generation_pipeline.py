import unittest

from app.core.results import ExecutionResult
from app.pipeline.generation_pipeline import GenerationPipeline
from app.pipeline.pipeline_context import PipelineContext
from app.pipeline.pipeline_manager import PipelineManager
from app.pipeline.pipeline_stage import PipelineStage
from app.pipeline.pipeline_state import PipelineState
from app.pipeline.stage_registry import StageRegistry


class RecordingStage(PipelineStage):
    def __init__(self, name, result=None, valid=True):
        self._name = name
        self.result = result if result is not None else {name: "done"}
        self.valid = valid
        self.rollback_calls = 0

    @property
    def name(self):
        return self._name

    def validate(self, context):
        return self.valid

    def execute(self, context):
        return self.result

    def rollback(self, context):
        self.rollback_calls += 1
        return True


class GenerationPipelineTests(unittest.TestCase):
    def test_context_carries_values_timeline_and_stage_results(self):
        context = PipelineContext("Build API")
        entry = context.begin_stage("plan")
        context.finish_stage(entry, ExecutionResult.completed({"plan": ["api"]}))
        context.merge({"plan": ["api"]})
        self.assertEqual(context.values["plan"], ["api"])
        self.assertEqual(context.completed_stages, ["plan"])
        self.assertEqual(context.stage_results["plan"]["status"], "completed")

    def test_registry_rejects_invalid_and_duplicate_stages(self):
        registry = StageRegistry()
        stage = RecordingStage("plan")
        registry.register(stage)
        with self.assertRaises(ValueError):
            registry.register(stage)
        with self.assertRaises(TypeError):
            registry.register(object())

    def test_manager_runs_all_stages_and_records_events_metrics(self):
        registry = StageRegistry()
        registry.register(RecordingStage("plan"))
        registry.register(RecordingStage("execute"))
        result = PipelineManager(registry).execute("Build API")
        self.assertTrue(result.success)
        self.assertEqual(result.status, "finished")
        self.assertEqual(result.completed_stages, ["plan", "execute"])
        self.assertEqual(result.metrics["pipeline_stages"], 2)
        self.assertIn("PIPELINE_STAGE_STARTED", [event["type"] for event in result.context.events])

    def test_failed_stage_rolls_back_completed_stages(self):
        first = RecordingStage("plan")
        failing = RecordingStage("execute", valid=False)
        registry = StageRegistry()
        registry.register(first)
        registry.register(failing)
        result = PipelineManager(registry).execute("Build API")
        self.assertFalse(result.success)
        self.assertEqual(result.failed_stage, "execute")
        self.assertEqual(first.rollback_calls, 1)
        self.assertEqual(result.context.state, PipelineState.FAILED)

    def test_resume_skips_completed_stages(self):
        first = RecordingStage("plan")
        second = RecordingStage("execute", valid=False)
        registry = StageRegistry()
        registry.register(first)
        registry.register(second)
        manager = PipelineManager(registry)
        interrupted = manager.execute("Build API")
        second.valid = True
        resumed = manager.resume(interrupted.context)
        self.assertTrue(resumed.success)
        self.assertEqual(resumed.completed_stages, ["plan", "execute"])

    def test_default_pipeline_produces_a_governed_preflight_and_report(self):
        result = GenerationPipeline().run("Build a web notes app with search")
        self.assertTrue(result.success)
        self.assertIn("engineering_brief", result.context.values)
        self.assertIn("report", result.context.values)
        self.assertEqual(result.status, "finished")

    def test_pipeline_waits_for_high_risk_or_payment_approval(self):
        result = GenerationPipeline().run("Build a web ecommerce app with login and checkout")
        self.assertFalse(result.success)
        self.assertEqual(result.status, "waiting")
        self.assertEqual(result.context.state, PipelineState.WAITING)
        self.assertIn("engineering_brief", result.context.values)

    def test_project_execution_pipeline_uses_injected_orchestrator_only_after_approval(self):
        class Orchestrator:
            def run_result(self, goal, project_path, context):
                self.context = context
                return ExecutionResult.completed({"goal": goal}, "Project completed", artifacts=[project_path])

        orchestrator = Orchestrator()
        result = GenerationPipeline.for_project_execution(orchestrator).run(
            "Build a web notes app with search", PipelineContext("Build a web notes app with search", project_path="workspace/notes")
        )
        self.assertTrue(result.success)
        self.assertIn("execution", result.context.values)
        self.assertIn("workspace/notes", result.artifacts)
        self.assertIn("planning_package", orchestrator.context["memory"])


if __name__ == "__main__":
    unittest.main()
