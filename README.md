# Jarvis-X

## Governed engineering intake

Before execution, a software goal can now be passed through a deterministic
requirements → architecture → risk → research → policy pipeline. See
[the engineering pipeline guide](docs/engineering-pipeline.md).

## Runtime kernel

The new additive runtime composition root supports lifecycle control,
priority/delayed jobs, watchdog timeouts, bounded retries, snapshots, and health
reporting. See [the runtime-kernel guide](docs/runtime-kernel.md).

## Autonomous generation pipeline

The composable [generation pipeline](docs/generation-pipeline.md) connects the
governed engineering brief to registered execution, repair, validation, and
reporting stages through one resumable context.

## Multi-project workspaces

[WorkspaceManager](docs/workspaces.md) provides persistent, isolated projects
with recoverable archive/delete actions, snapshots, lifecycle events, metrics,
and CLI support.

## Intelligent analysis

The [analyst layer](docs/intelligent-analysis.md) creates a complete planning
package—intent, requirements, questions, architecture, stack comparison,
database/API design, complexity, risk, and cost—before execution begins.

## Multi-agent collaboration (Phase 1)

Jarvis-X now exposes a specialized project workflow:

```text
Planner → Coder → Tester → Reviewer → Documentation
```

Use it through `ProjectManager`:

```python
from app.project.project_manager import ProjectManager

result = ProjectManager().execute_collaboration("Create a small notes app")
print(result["success"], result["timeline"])
```

Each run shares `goal`, `project_path`, `plan`, `current_step`, and `memory`
through one context object. The orchestrator routes work via `MessageBus`,
tracks pending/running/completed/failed tasks, publishes lifecycle events, and
records a timestamped execution timeline.

Tester or reviewer failures are routed back to the coder for repair; planner
failures retry; documentation failures are recorded without invalidating an
otherwise validated project.

## Autonomous Software Engineer (Sprint 2)

`BrainPipeline` now prepares an engineering brief before any project work:

```python
from app.brain.brain_pipeline import BrainPipeline

brief = BrainPipeline().prepare("Build a web notes app with login")
print(brief["strategy"]["selected"])
print(brief["simulation"])
```

The brief adds ranked implementation strategies, simulated file/dependency/risk
estimates, cost and optimization suggestions, and an optimized declarative
execution plan. It is pre-execution only: the existing project and agent
orchestrators retain responsibility for approved file changes.

## Golden Benchmark Suite

The release catalog provides twenty stable project briefs across basic,
intermediate, advanced, and expert tiers. It validates the full pre-execution
engineering brief (requirements, architecture, strategy, simulation, and
verification plan) without generating files or calling an LLM.

```python
from app.autonomy.brain_layer import AutonomousBrainLayer

report = AutonomousBrainLayer().run_golden_benchmarks()
print(report["preflight_rate"], report["quality_gate"])
```

Projects involving payments are intentionally reported as `needs_approval`;
they count as successful safe preflights rather than autonomous execution.

## Shared engineering contract

New integration boundaries can return `ExecutionResult`, a consistent response
containing `success`, `status`, `message`, `data`, `metrics`, `warnings`,
`errors`, `artifacts`, and `duration`. Existing methods keep their current
return values while standardized entry points are adopted incrementally:

```python
brief_result = BrainPipeline().prepare_result("Build a web notes app")
run_result = ProjectManager().execute_collaboration_result("Build a notes app")
```

`JarvisContext` supplies the shared goal, project path, current step, memory,
metrics, artifacts, events, and timeline. `SharedContext` builds on it for the
existing multi-agent workflow.

## Release pipeline

Run the auditable release gates from the project root:

```powershell
python -m app.release.cli release --output artifacts/releases --version 0.1.0-alpha
```

The release checks the unit suite, Golden Benchmark preflight, required
documentation, and high-confidence security signals in the shipped `app/`
package. It writes a JSON manifest and Markdown report. Add `--package` to
create a ZIP only after all gates pass.

## Semantic memory

`SemanticMemoryManager` stores verified engineering outcomes in a local JSON
file and recalls them by meaning, tags, importance, and confidence. The
governed engineering brief exposes relevant read-only results as
`semantic_context`; preparing a brief does not add or alter memories.

```python
from app.semantic_memory import SemanticMemoryManager

memory = SemanticMemoryManager()
memory.record_outcome("FastAPI JWT authentication", True, tags=["fastapi", "authentication"])
print(memory.search("secure API login"))
```

## Dynamic workflow selection

`WorkflowEngine` selects lifecycle stages from project scope, ambiguity, risk,
and deployment intent. `BrainPipeline.prepare()` includes its read-only
selection as `workflow`; it does not execute any step. A workflow runs only
handlers explicitly registered by the application.
