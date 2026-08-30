"""Execution planner for engineering workflow.

Converts resolved tasks into executable phases with resource
allocation, milestones, and rollback strategies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ExecutionPhase:
    """A single execution phase."""

    id: str
    name: str
    description: str
    tasks: List[str] = field(default_factory=list)
    estimated_hours: float = 0.0
    milestones: List[str] = field(default_factory=list)
    rollback_strategy: str = ""
    parallel: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tasks": list(self.tasks),
            "estimated_hours": round(self.estimated_hours, 1),
            "milestones": list(self.milestones),
            "rollback_strategy": self.rollback_strategy,
            "parallel": self.parallel,
        }


@dataclass
class ExecutionPlan:
    """Complete execution plan with phases."""

    project_name: str
    phases: List[ExecutionPhase] = field(default_factory=list)
    total_phases: int = 0
    total_estimated_hours: float = 0.0
    critical_path: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project_name": self.project_name,
            "phases": [p.to_dict() for p in self.phases],
            "total_phases": self.total_phases,
            "total_estimated_hours": round(self.total_estimated_hours, 1),
            "critical_path": list(self.critical_path),
        }


class ExecutionPlanner:
    """Create execution plan from resolved tasks.

    Groups tasks into phases, allocates resources, and defines
    milestones and rollback strategies.
    """

    # Standard execution phases
    PHASE_TEMPLATES = {
        "Phase 1 - Foundation": {
            "categories": ["setup"],
            "description": "Initialize project structure and development environment",
            "milestones": ["Project initialized", "CI/CD ready", "Dev environment configured"],
            "rollback": "Rollback to git HEAD, preserve branch",
        },
        "Phase 2 - Core Backend": {
            "categories": ["backend"],
            "description": "Build backend services, APIs, and database",
            "milestones": ["API endpoints functional", "Database schema created", "Auth working"],
            "rollback": "Rollback database migrations, restore API code",
        },
        "Phase 3 - Frontend": {
            "categories": ["frontend"],
            "description": "Build user interface and client-side logic",
            "milestones": ["UI components ready", "API integration complete", "Routing working"],
            "rollback": "Rollback to last working frontend commit",
        },
        "Phase 4 - Quality Assurance": {
            "categories": ["testing"],
            "description": "Write and run tests, ensure quality gates",
            "milestones": ["Unit tests passing", "Integration tests passing", "Coverage > 80%"],
            "rollback": "Skip failing tests, deploy with warnings",
        },
        "Phase 5 - Deployment": {
            "categories": ["deployment"],
            "description": "Deploy to production with monitoring",
            "milestones": ["Production deployed", "SSL configured", "Monitoring active"],
            "rollback": "Rollback to previous stable version",
        },
        "Phase 6 - Documentation": {
            "categories": ["documentation"],
            "description": "Write comprehensive documentation",
            "milestones": ["README complete", "API docs generated", "Deploy guide ready"],
            "rollback": "N/A - documentation only",
        },
    }

    def plan(self, task_breakdown, resolved_dependencies) -> ExecutionPlan:
        """Create execution plan from task breakdown.

        Args:
            task_breakdown: TaskBreakdown from breakdown engine.
            resolved_dependencies: ResolvedDependencies from resolver.

        Returns:
            ExecutionPlan with phases.
        """
        phases = []
        task_map = {t.id: t for t in task_breakdown.tasks}

        # Group tasks by category
        tasks_by_category: dict = {}
        for task in task_breakdown.tasks:
            cat = task.category
            if cat not in tasks_by_category:
                tasks_by_category[cat] = []
            tasks_by_category[cat].append(task)

        # Create phases
        phase_id = 1
        for phase_name, phase_config in self.PHASE_TEMPLATES.items():
            categories = phase_config["categories"]
            phase_tasks = []
            for cat in categories:
                phase_tasks.extend(tasks_by_category.get(cat, []))

            if phase_tasks:
                phase = ExecutionPhase(
                    id=f"PHASE-{phase_id:02d}",
                    name=phase_name,
                    description=phase_config["description"],
                    tasks=[t.id for t in phase_tasks],
                    estimated_hours=sum(t.estimated_hours for t in phase_tasks),
                    milestones=phase_config["milestones"],
                    rollback_strategy=phase_config["rollback"],
                    parallel=resolved_dependencies.parallel_groups and len(resolved_dependencies.parallel_groups) > 1,
                )
                phases.append(phase)
                phase_id += 1

        # Add domain-specific phase if needed
        domain_tasks = [t for t in task_breakdown.tasks if t.category == "domain_specific"]
        if domain_tasks:
            phases.append(ExecutionPhase(
                id=f"PHASE-{phase_id:02d}",
                name="Phase 7 - Domain Features",
                description="Implement domain-specific features and business logic",
                tasks=[t.id for t in domain_tasks],
                estimated_hours=sum(t.estimated_hours for t in domain_tasks),
                milestones=["Domain features complete", "Business logic verified"],
                rollback_strategy="Rollback to Phase 2 state",
                parallel=False,
            ))

        plan = ExecutionPlan(
            project_name=task_breakdown.project_name,
            phases=phases,
            total_phases=len(phases),
            total_estimated_hours=sum(p.estimated_hours for p in phases),
            critical_path=resolved_dependencies.critical_path,
        )
        return plan
