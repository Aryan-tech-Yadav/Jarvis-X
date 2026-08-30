# Intelligent requirement and architecture analysis

`AnalysisEngine` turns a natural-language goal into the structured planning
package that planners and execution agents consume. It is deterministic and
evidence-based: existing requirement, architecture, risk, and cost findings are
preserved rather than being silently replaced.

```python
from app.analysis import AnalysisEngine

report = AnalysisEngine().analyze(
    "Build a hospital web system with appointment scheduling, billing, Docker, and CI/CD"
)
package = report["planning_package"]
print(package["intent"])
print(package["database"]["entities"])
print(package["api"]["endpoints"])
```

The package includes intent, functional and non-functional requirements,
missing-information questions, stack comparison and selected stack, database
entities/relationships, API endpoints, architecture rationale, complexity,
risk, cost, and timeline inputs. `BrainPipeline.prepare()` exposes it as
`planning_package`; `CollaborationStage` passes it to agents in the shared
execution context (`memory["planning_package"]`).

High-risk goals continue to wait at the governance gate before any project
execution stage is entered.
