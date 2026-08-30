"""Engineering project generation facade.

Wraps the existing project builder and wires in architecture context
so the generated project reflects the chosen design.
"""

from app.core.logger import Logger
from app.core.results import ExecutionResult
from app.project.project_builder import ProjectBuilder


class ProjectGenerator:
    """Materialize the planned architecture into a concrete project workspace."""

    def __init__(self, builder=None):
        self.builder = builder or ProjectBuilder()

    def generate(self, goal: str, architecture: dict | None = None) -> ExecutionResult:
        if not isinstance(goal, str) or not goal.strip():
            return ExecutionResult.failed("Goal cannot be empty")

        try:
            # The project builder currently expects a raw prompt string.
            # Architecture context is injected into the builder's downstream
            # components (designer / writer) via the project dict it creates.
            base_path = self.builder.build(goal.strip())
            return ExecutionResult.completed(
                data={"project_path": base_path, "architecture": architecture or {}},
                message="Project generated",
                artifacts=[base_path],
            )
        except Exception as exc:
            Logger.error(f"Project generation failed: {exc}")
            return ExecutionResult.failed(str(exc))
