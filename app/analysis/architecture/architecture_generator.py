from app.architecture.architecture_engine import ArchitectureEngine

from ..models.architecture_model import ArchitectureModel
from .api_designer import APIDesigner
from .database_designer import DatabaseDesigner
from .tech_stack_selector import TechStackSelector


class ArchitectureGenerator:
    def __init__(self, architecture=None, tech_stack=None, database=None, api=None):
        self.architecture = architecture or ArchitectureEngine()
        self.tech_stack = tech_stack or TechStackSelector()
        self.database = database or DatabaseDesigner()
        self.api = api or APIDesigner()

    def generate(self, goal, requirements, intent, base_requirements=None, base_architecture=None):
        base_requirements = base_requirements or {"features": requirements.functional, "constraints": requirements.constraints}
        base = base_architecture or self.architecture.design(base_requirements)
        stack = self.tech_stack.select(requirements, intent)
        database = self.database.design(goal, requirements)
        api = self.api.design(requirements)
        model = ArchitectureModel(base["pattern"], stack["selected"]["components"], database["entities"], database["relationships"],
                                  api["endpoints"], base["rationale"])
        return {**model.to_dict(), "stack_comparison": stack["candidates"], "base": base}
