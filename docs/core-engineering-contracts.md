# Core engineering contracts

Jarvis-X is migrating integration boundaries to two shared core models without
breaking existing module APIs.

`ExecutionResult` is the standard product-facing result shape:

```python
{
    "success": True,
    "status": "completed",
    "message": "Engineering brief prepared",
    "data": {},
    "metrics": {},
    "warnings": [],
    "errors": [],
    "artifacts": [],
    "duration": 0.0,
}
```

`JarvisContext` owns shared lifecycle state: goal, project path, current step,
memory, metrics, warnings, errors, artifacts, events, and a timeline.
`SharedContext` inherits this common state while retaining the existing
project-specific planning, validation, reflection, and agent-progress fields.

For safe migration, legacy interfaces remain available. Use
`BrainPipeline.prepare_result()` for governed pre-execution work and
`AgentOrchestrator.run_result()` or
`ProjectManager.execute_collaboration_result()` for multi-agent execution.
Each adapts the existing result rather than changing it in place.
