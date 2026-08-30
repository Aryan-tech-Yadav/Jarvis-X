from time import perf_counter

from app.core.results import ExecutionResult
from app.events.event_bus import EventBus

from .pipeline_context import PipelineContext
from .pipeline_result import PipelineResult
from .pipeline_state import PipelineState


class PipelineManager:
    """Executes registered stages with validation, rollback, metrics, and resume."""

    def __init__(self, registry, event_bus=None):
        self.registry = registry
        self.event_bus = event_bus or EventBus()

    def execute(self, prompt=None, context=None, *, resume=False):
        context = self._context(prompt, context)
        if context.state == PipelineState.WAITING and not resume:
            return self._result(False, "waiting", context, warnings=["Pipeline is waiting for approval or input."])
        context.state = PipelineState.RUNNING
        for stage in self.registry.stages():
            if resume and stage.name in context.completed_stages:
                continue
            result = self._run_stage(stage, context)
            if result.status == "waiting":
                context.state = PipelineState.WAITING
                return self._result(False, "waiting", context, warnings=result.warnings or [result.message])
            if not result.success:
                context.state = PipelineState.FAILED
                context.failed_stage = stage.name
                rollback_errors = self.rollback(context)
                return self._result(False, "failed", context, errors=[*result.errors, *rollback_errors])
        context.state = PipelineState.FINISHED
        return self._result(True, "finished", context)

    def resume(self, context):
        if not isinstance(context, PipelineContext):
            raise TypeError("resume requires PipelineContext")
        context.state = PipelineState.RECOVERING
        return self.execute(context=context, resume=True)

    def rollback(self, context):
        errors = []
        for name in reversed(context.completed_stages):
            stage = self.registry.get(name)
            if stage is None:
                continue
            result = ExecutionResult.timed(stage.rollback, context)
            self._publish("PIPELINE_STAGE_ROLLED_BACK", context, {"stage": name, "success": result.success})
            if not result.success:
                errors.extend(result.errors or [result.message])
        return errors

    def _run_stage(self, stage, context):
        entry = context.begin_stage(stage.name)
        self._publish("PIPELINE_STAGE_STARTED", context, {"stage": stage.name})
        started = perf_counter()
        validation = ExecutionResult.timed(stage.validate, context)
        result = validation if not validation.success else ExecutionResult.timed(stage.execute, context)
        duration = perf_counter() - started
        result.duration = duration
        result.metrics = {**stage.metrics(), **result.metrics, "duration_seconds": duration}
        context.add_metric("pipeline_stages")
        context.add_metric("pipeline_duration_seconds", duration)
        context.finish_stage(entry, result)
        if result.success and isinstance(result.data, dict):
            context.merge(result.data)
            context.artifacts.extend(item for item in result.artifacts if item not in context.artifacts)
            context.warnings.extend(item for item in result.warnings if item not in context.warnings)
        elif not result.success:
            context.errors.extend(item for item in result.errors if item not in context.errors)
        self._publish("PIPELINE_STAGE_COMPLETED" if result.success else "PIPELINE_STAGE_FAILED", context,
                      {"stage": stage.name, "success": result.success, "duration": duration})
        return result

    def _result(self, success, status, context, warnings=None, errors=None):
        return PipelineResult(success, status, context, list(context.completed_stages), context.failed_stage,
                              dict(context.metrics), list(context.artifacts), list(warnings or context.warnings),
                              list(errors or context.errors))

    def _publish(self, event_type, context, payload):
        event = self.event_bus.publish(event_type, payload)
        context.events.append(event.to_dict())

    @staticmethod
    def _context(prompt, context):
        if context is not None:
            if not isinstance(context, PipelineContext):
                raise TypeError("context must be PipelineContext")
            return context
        return PipelineContext(prompt)
