"""Integration boundary for the Autonomous Brain Layer sprint.

This façade records the intelligence signals around an execution. It deliberately
does not replace the existing router, project manager, or reasoning loop.
"""

from app.dashboard.dashboard_data import DashboardData
from app.dashboard.dashboard_metrics import DashboardMetrics
from app.knowledge.knowledge_base import KnowledgeBase
from app.learning.learning_database import LearningDatabase
from app.learning.learning_optimizer import LearningOptimizer
from app.memory.memory_index import MemoryIndex
from app.memory.memory_search import MemorySearch
from app.reflection.reflection_agent import ReflectionAgent
from app.task.task import AutonomousTask
from app.task.task_scheduler import TaskScheduler
from app.brain.brain_pipeline import BrainPipeline
from app.benchmark.golden_benchmark_runner import GoldenBenchmarkRunner


class AutonomousBrainLayer:
    def __init__(self, memory=None, knowledge=None, scheduler=None, learning=None, reflection=None, pipeline=None):
        self.memory = memory or MemoryIndex()
        self.memory_search = MemorySearch(self.memory)
        self.knowledge = knowledge or KnowledgeBase()
        self.scheduler = scheduler or TaskScheduler()
        self.learning = learning or LearningDatabase()
        self.reflection = reflection or ReflectionAgent()
        self.dashboard_data = DashboardData()
        self.dashboard_metrics = DashboardMetrics()
        self.executions = []
        self.pipeline = pipeline or BrainPipeline()

    def prepare(self, goal, context=""):
        task = AutonomousTask(goal)
        self.scheduler.submit(task)
        return {
            "task": task,
            "memory": self.memory_search.search(goal),
            "knowledge": self.knowledge.search(goal),
            "context": context,
        }

    def prepare_engineering_goal(self, goal):
        """Return a governed pre-execution brief for a software-engineering goal."""
        return self.pipeline.prepare(goal)

    def record_execution(self, goal, success, *, reflection_scores=None, repaired=False):
        self.memory.add(goal, kind="execution", priority=3 if success else 1, importance=1.0 if success else 0.5)
        outcome = {"area": "runtime_repair" if repaired else "execution", "success": bool(success), "goal": goal}
        self.learning.record(outcome)
        reflection = self.reflection.scorecard(reflection_scores or {})
        event = {"goal": goal, "success": bool(success), "repaired": bool(repaired), "reflection": reflection}
        self.executions.append(event)
        return event

    def dashboard(self):
        successes = sum(item["success"] for item in self.executions)
        data = self.dashboard_data.collect(
            projects=len(self.executions), successes=successes, failures=len(self.executions) - successes,
            repairs=sum(item["repaired"] for item in self.executions), memory_entries=len(self.memory.entries()),
            learning_events=self.learning.count(),
        )
        return self.dashboard_metrics.calculate(data)

    def improvement_plan(self):
        return LearningOptimizer(self.learning).recommend()

    def run_golden_benchmarks(self, tier=None, *, execute=False, execution_handler=None):
        """Evaluate release readiness without creating projects by default."""
        return GoldenBenchmarkRunner().run(tier=tier, execute=execute, execution_handler=execution_handler)
