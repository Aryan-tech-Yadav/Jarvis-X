# Autonomous generation pipeline

`GenerationPipeline` provides the common execution contract for a project run:

```text
prompt → governed engineering brief → registered execution stages → final report
```

Every stage validates and returns a shared `ExecutionResult`. `PipelineContext`
records inputs, outputs, metrics, events, timeline entries, artifacts, warnings,
and errors. On a failure, completed stages are rolled back in reverse order; a
context can then be resumed without repeating its completed stages.

The default pipeline is intentionally a safe preflight plus final report—it
does not write a project. For an explicit project-generation run, compose the
existing multi-agent orchestrator:

```python
from app.pipeline import GenerationPipeline, PipelineContext

pipeline = GenerationPipeline.for_project_execution()
context = PipelineContext("Build a web notes app with search", project_path="workspace/notes")
result = pipeline.run(context.goal, context)

if result.status == "waiting":
    # Resolve the governance approval before resuming.
    print(result.warnings)
```

The executor stage is never created by the safe default pipeline. This preserves
the existing governance gate: high-risk and payment workloads wait for approval
before any project-writing orchestration can run.
