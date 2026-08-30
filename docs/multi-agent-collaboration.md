# Multi-agent collaboration

`AgentOrchestrator` is the Phase 1 project execution entry point. Its default
registry contains `PlannerAgent`, `CoderAgent`, `TesterAgent`, `ReviewerAgent`,
and `DocumentationAgent`.

Agents communicate through `MessageBus`; the orchestrator is the only component
that controls their order. Results include the shared context, event history,
and a timeline suitable for a future GUI.

```python
from app.orchestrator.agent_orchestrator import AgentOrchestrator

result = AgentOrchestrator(max_retries=1).run("Build a calculator")
```

The coder delegates create/modify/repair work to `ProjectManager`. The tester
returns `{ "passed": bool, "errors": list }`, the reviewer is read-only, and
the documentation agent maintains a project's `README.md`, `CHANGELOG.md`, and
`docs/latest-feature.md` after successful work.
