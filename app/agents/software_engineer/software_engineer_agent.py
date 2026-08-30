"""Senior software-engineering analysis agent for EOS."""

from typing import Any, Dict, Optional

from app.eos.base_agent import BaseAgent
from app.eos.result import AgentResult
from app.agents.software_engineer.architecture_designer import ArchitectureDesigner
from app.agents.software_engineer.dependency_analyzer import DependencyAnalyzer
from app.agents.software_engineer.estimator import Estimator
from app.agents.software_engineer.project_planner import ProjectPlanner
from app.agents.software_engineer.requirement_analyzer import RequirementAnalyzer
from app.agents.software_engineer.task_breaker import TaskBreaker
from app.agents.software_engineer.technology_selector import TechnologySelector


class SoftwareEngineerAgent(BaseAgent):
    """Analyze, design, plan, and estimate a project before coding begins."""

    name = "Software Engineer Agent"
    version = "1.0"
    capabilities = ("analyze_requirements", "design_architecture", "plan_project", "estimate_project")

    def __init__(
        self,
        requirement_analyzer: Optional[RequirementAnalyzer] = None,
        architecture_designer: Optional[ArchitectureDesigner] = None,
        project_planner: Optional[ProjectPlanner] = None,
        task_breaker: Optional[TaskBreaker] = None,
        dependency_analyzer: Optional[DependencyAnalyzer] = None,
        technology_selector: Optional[TechnologySelector] = None,
        estimator: Optional[Estimator] = None,
    ):
        super().__init__()
        self.requirement_analyzer = requirement_analyzer or RequirementAnalyzer()
        self.architecture_designer = architecture_designer or ArchitectureDesigner()
        self.project_planner = project_planner or ProjectPlanner()
        self.task_breaker = task_breaker or TaskBreaker()
        self.dependency_analyzer = dependency_analyzer or DependencyAnalyzer()
        self.technology_selector = technology_selector or TechnologySelector()
        self.estimator = estimator or Estimator()

    def execute(self, task: Any) -> AgentResult:
        goal = self._goal_from(task)
        requirements = self.requirement_analyzer.analyze(goal)
        technology = self.technology_selector.select(requirements)
        requirements.tech_stack = technology.to_dict()
        architecture = self.architecture_designer.design(requirements)
        plan = self.project_planner.plan(goal)
        breakdown = self.task_breaker.break_down(architecture, requirements)
        dependencies = self.dependency_analyzer.analyze([item.to_dict() for item in breakdown.tasks])
        estimate = self.estimator.estimate(requirements, architecture, technology)
        output: Dict[str, Any] = {
            "goal": goal,
            "requirements": requirements.to_dict(),
            "architecture": architecture.to_dict(),
            "technology": technology.to_dict(),
            "plan": getattr(plan, "data", plan),
            "tasks": breakdown.to_dict(),
            "dependencies": dependencies.to_dict(),
            "estimate": estimate.to_dict(),
            "coding_started": False,
        }
        return AgentResult(success=True, output=output, agent=self.name)

    @staticmethod
    def _goal_from(task: Any) -> str:
        if isinstance(task, str):
            goal = task
        elif isinstance(task, dict):
            goal = task.get("entity") or task.get("goal") or task.get("parameters", {}).get("goal", "")
        else:
            goal = getattr(task, "entity", None) or getattr(task, "goal", "")
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("Software engineering task requires a project goal")
        return goal.strip()

