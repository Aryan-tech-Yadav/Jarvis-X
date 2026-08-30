"""Project planning facade."""

from app.engineering.project_planner import ProjectPlanner as EngineeringProjectPlanner


class ProjectPlanner:
    def __init__(self, planner=None):
        self.planner = planner or EngineeringProjectPlanner()

    def plan(self, goal: str):
        return self.planner.plan(goal)

