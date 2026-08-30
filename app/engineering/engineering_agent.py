"""Autonomous Software Engineering Agent.

EngineeringAgent is the CEO of Jarvis-X's software engineering pipeline.
It now delegates to EngineeringPipeline for the full lifecycle.
"""

from app.engineering.engineering_pipeline import EngineeringPipeline
from app.core.logger import Logger
from app.core.results import ExecutionResult


class EngineeringAgent:
    """Orchestrate the autonomous software engineering lifecycle."""

    def __init__(
        self,
        pipeline=None,
    ):
        self.pipeline = pipeline or EngineeringPipeline()

    def execute(self, goal: str) -> ExecutionResult:
        """Run the full engineering pipeline against a user goal."""
        Logger.info(f"[EngineeringAgent] Delegating to pipeline for: {goal}")
        return self.pipeline.run(goal)

    # Backwards compatibility alias used by BrainManager
    run = execute
