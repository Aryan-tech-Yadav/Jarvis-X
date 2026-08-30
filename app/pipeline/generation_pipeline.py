from app.brain.brain_pipeline import BrainPipeline
from app.core.results import ExecutionResult
from app.orchestrator.agent_orchestrator import AgentOrchestrator

from .pipeline_manager import PipelineManager
from .pipeline_stage import PipelineStage
from .stage_registry import StageRegistry


class EngineeringBriefStage(PipelineStage):
    name = "engineering_brief"

    def __init__(self, brain=None):
        self.brain = brain or BrainPipeline()

    def execute(self, context):
        result = self.brain.prepare_result(context.goal)
        if not result.success:
            return result
        brief = result.data
        payload = {"engineering_brief": brief}
        if not brief["approval"]["approved"]:
            return ExecutionResult(True, "waiting", "Engineering brief requires approval", payload,
                                   warnings=list(brief["approval"]["reasons"]), metrics=result.metrics)
        return ExecutionResult.completed(payload, result.message, metrics=result.metrics, warnings=result.warnings,
                                         artifacts=result.artifacts, duration=result.duration)


class CollaborationStage(PipelineStage):
    name = "multi_agent_execution"

    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator or AgentOrchestrator()

    def validate(self, context):
        if not context.values.get("engineering_brief", {}).get("approval", {}).get("approved"):
            return ExecutionResult.failed("Execution requires an approved engineering brief")
        return super().validate(context)

    def execute(self, context):
        package = context.values["engineering_brief"]["planning_package"]
        execution_context = {
            "goal": context.goal,
            "project_path": context.project_path,
            "memory": {"planning_package": package},
        }
        result = self.orchestrator.run_result(context.goal, context.project_path, execution_context)
        if result.success and isinstance(result.data, dict):
            return ExecutionResult.completed({"execution": result.data}, result.message, metrics=result.metrics,
                                             warnings=result.warnings, artifacts=result.artifacts, duration=result.duration)
        return result


class FinalReportStage(PipelineStage):
    name = "final_report"

    def execute(self, context):
        report = {
            "goal": context.goal,
            "completed_stages": [*context.completed_stages, self.name],
            "warnings": list(context.warnings),
            "timeline": list(context.timeline),
            "metrics": dict(context.metrics),
        }
        return ExecutionResult.completed({"report": report}, "Generation report prepared", artifacts=[report])


class GenerationPipeline:
    """Factory for a safe preflight pipeline or an explicitly enabled build flow."""

    def __init__(self, stages=None, event_bus=None):
        self.registry = StageRegistry()
        for stage in stages or (EngineeringBriefStage(), FinalReportStage()):
            self.registry.register(stage)
        self.manager = PipelineManager(self.registry, event_bus)

    @classmethod
    def for_project_execution(cls, orchestrator=None, event_bus=None):
        return cls((EngineeringBriefStage(), CollaborationStage(orchestrator), FinalReportStage()), event_bus)

    def run(self, prompt, context=None):
        return self.manager.execute(prompt, context)

    def resume(self, context):
        return self.manager.resume(context)
