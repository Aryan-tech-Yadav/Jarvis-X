"""Engineering package."""

from app.engineering.workflow import EngineeringWorkflow, EngineeringWorkflowResult
from app.engineering.execution_engine import ExecutionEngine, ExecutionPolicy
from app.engineering.project_type_detector import ProjectTypeDetector, ProjectDetection, ProjectType, TechStack
from app.engineering.planning_validator import PlanningValidator, ValidationResult, ValidationIssue
from app.engineering.engineering_brain import EngineeringBrain, EngineeringDecisionReport
from app.engineering.decision_intelligence import DecisionIntelligenceEngine, DecisionOption, DecisionPackage

__all__ = [
    "EngineeringWorkflow",
    "EngineeringWorkflowResult",
    "AutonomousExecutor",
    "ExecutionMetrics",
    "RefinementCycle",
    "ExecutionEngine",
    "ExecutionPolicy",
    "ProjectTypeDetector",
    "ProjectDetection",
    "ProjectType",
    "TechStack",
    "PlanningValidator",
    "ValidationResult",
    "ValidationIssue",
    "EngineeringBrain",
    "EngineeringDecisionReport",
    "DecisionIntelligenceEngine",
    "DecisionOption",
    "DecisionPackage",
]


def __getattr__(name):
    """Load the autonomous executor lazily to avoid agent import cycles."""
    if name in {"AutonomousExecutor", "ExecutionMetrics", "RefinementCycle"}:
        from app.engineering.autonomous_executor import (
            AutonomousExecutor,
            ExecutionMetrics,
            RefinementCycle,
        )
        return {
            "AutonomousExecutor": AutonomousExecutor,
            "ExecutionMetrics": ExecutionMetrics,
            "RefinementCycle": RefinementCycle,
        }[name]
    raise AttributeError(name)
