from app.optimizer.dependency_optimizer import DependencyOptimizer
from app.optimizer.parallel_optimizer import ParallelOptimizer
from app.optimizer.step_merger import StepMerger
from app.optimizer.step_splitter import StepSplitter


class ExecutionOptimizer:
    """Optimizes a declarative plan; it never runs tasks itself."""

    def __init__(self, merger=None, splitter=None, dependencies=None, parallel=None):
        self.merger = merger or StepMerger()
        self.splitter = splitter or StepSplitter()
        self.dependencies = dependencies or DependencyOptimizer()
        self.parallel = parallel or ParallelOptimizer()

    def optimize(self, steps):
        normalized = [dict(step) if isinstance(step, dict) else {"name": str(step)} for step in steps]
        split = self.splitter.split(normalized)
        ordered = self.dependencies.order(split)
        merged = self.merger.merge(ordered)
        return {"steps": merged, "parallel_groups": self.parallel.groups(merged), "estimated_step_reduction": max(0, len(normalized) - len(merged))}
