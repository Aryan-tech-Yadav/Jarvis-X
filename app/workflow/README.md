# Workflow Engine

The workflow engine selects a dependency-aware engineering lifecycle from a
goal's requirements, risk, and simulation signals. It is safe by default:
preparing a workflow has no side effects, and execution runs only handlers that
the caller explicitly registers.

`BrainPipeline` publishes the selected workflow in its governed briefing. The
workflow is advisory until a caller provides real stage handlers.
