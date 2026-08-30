# Governed engineering pipeline

`BrainPipeline` provides the pre-execution control plane for Jarvis-X:

```text
goal → requirements → architecture → risk → research → policy gate → audit trail
```

It is deterministic and side-effect free: it does not call an LLM, run tools, or
create files. A caller should pass an approved brief to the existing project or
agent orchestrator. High-risk goals and invalid briefs are deliberately held for
human approval.

```python
from app.brain.brain_pipeline import BrainPipeline

brief = BrainPipeline().prepare("Build a web ecommerce app with login and checkout")
if brief["approval"]["approved"]:
    # Hand the goal to ProjectManager or AgentOrchestrator.
    pass
```

The returned brief includes chosen architecture, technology rationale, feature
priorities, risks and mitigations, baseline best-practice citations, and a
structured audit trail.
