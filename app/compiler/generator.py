"""End-to-end deterministic compiler facade."""

from typing import Dict

from .optimizer import SpecOptimizer
from .parser import DSLParser
from .planner import WorkflowPlanner
from .semantic import SemanticValidator


class DSLGenerator:
    def __init__(self, parser=None, validator=None, optimizer=None, planner=None):
        self.parser = parser or DSLParser()
        self.validator = validator or SemanticValidator()
        self.optimizer = optimizer or SpecOptimizer()
        self.planner = planner or WorkflowPlanner()

    def compile(self, source: str) -> Dict[str, object]:
        spec = self.optimizer.optimize(self.parser.parse(source))
        self.validator.validate(spec)
        return {"specification": spec.to_dict(), "workflow": self.planner.plan(spec).to_dict()}

