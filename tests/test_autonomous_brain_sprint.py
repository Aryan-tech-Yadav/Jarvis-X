import time
import unittest

from app.dashboard.dashboard_data import DashboardData
from app.dashboard.dashboard_metrics import DashboardMetrics
from app.dashboard.dashboard_report import DashboardReport
from app.autonomy.brain_layer import AutonomousBrainLayer
from app.knowledge.knowledge_base import KnowledgeBase
from app.learning.learning_database import LearningDatabase
from app.learning.learning_optimizer import LearningOptimizer
from app.memory.memory_cleaner import MemoryCleaner
from app.memory.memory_compressor import MemoryCompressor
from app.memory.memory_index import MemoryIndex
from app.memory.memory_search import MemorySearch
from app.reasoning.reasoning_cache import ReasoningCache
from app.reasoning.reasoning_ranker import ReasoningRanker
from app.reasoning.reasoning_engine import ReasoningEngine
from app.reflection.reflection_report import ReflectionReport
from app.reflection.reflection_score import ReflectionScore
from app.task.task import AutonomousTask
from app.task.task_graph import TaskGraph
from app.task.task_scheduler import TaskScheduler
from app.tools.tool_cache import ToolCache
from app.tools.tool_ranker import ToolRanker


class AutonomousBrainSprintTests(unittest.TestCase):
    def test_memory_index_suppresses_duplicates(self):
        index = MemoryIndex()
        first = index.add("Python decorators wrap functions")
        self.assertEqual(first["id"], index.add("Python decorators wrap functions")["id"])

    def test_memory_search_ranks_keyword_and_priority(self):
        index = MemoryIndex()
        index.add("Python decorators wrap functions", priority=1)
        important = index.add("Python decorators preserve metadata", priority=5)
        self.assertEqual(MemorySearch(index).search("python decorators")[0]["id"], important["id"])

    def test_memory_compression_keeps_a_summary(self):
        entries = [{"content": "message " + str(number), "kind": "conversation"} for number in range(4)]
        summary = MemoryCompressor(max_entries=2).compress(entries)
        self.assertTrue(summary["compressed"])
        self.assertIn("message 0", summary["summary"])

    def test_memory_cleaner_removes_expired_and_low_priority_entries(self):
        entries = [{"id": "old", "content": "old", "created_at": 0, "priority": 0}, {"id": "new", "content": "new", "created_at": time.time(), "priority": 1}]
        cleaned = MemoryCleaner(max_age_seconds=10).clean(entries)
        self.assertEqual([entry["id"] for entry in cleaned], ["new"])

    def test_knowledge_base_indexes_categories_and_related_facts(self):
        knowledge = KnowledgeBase()
        tkinter = knowledge.add_fact("Tkinter is a Python GUI toolkit", category="gui", topics=["tkinter", "python"])
        python = knowledge.add_fact("Python supports desktop applications", category="language", topics=["python"])
        self.assertEqual(knowledge.search("Tkinter")[0]["id"], tkinter["id"])
        self.assertEqual(knowledge.related(tkinter["id"])[0]["id"], python["id"])

    def test_knowledge_cache_returns_cached_query(self):
        knowledge = KnowledgeBase()
        knowledge.add_fact("FastAPI creates web APIs", category="web")
        first = knowledge.search("FastAPI")
        second = knowledge.search("FastAPI")
        self.assertEqual(first, second)
        self.assertEqual(knowledge.cache.hits, 1)

    def test_task_graph_returns_independent_tasks_together(self):
        graph = TaskGraph()
        graph.add(AutonomousTask("setup", task_id="setup"))
        graph.add(AutonomousTask("api", task_id="api", dependencies=["setup"]))
        graph.add(AutonomousTask("ui", task_id="ui", dependencies=["setup"]))
        graph.complete("setup")
        self.assertEqual({task.task_id for task in graph.ready()}, {"api", "ui"})

    def test_task_scheduler_retries_then_completes(self):
        scheduler = TaskScheduler(TaskGraph())
        task = AutonomousTask("build", task_id="build", max_retries=1)
        scheduler.submit(task)
        scheduler.fail("build", "temporary")
        self.assertEqual(scheduler.next_batch()[0].status, "running")
        scheduler.complete("build", "done")
        self.assertEqual(task.status, "completed")

    def test_task_graph_rejects_unknown_dependency(self):
        graph = TaskGraph()
        with self.assertRaises(ValueError):
            graph.add(AutonomousTask("bad", dependencies=["missing"]))

    def test_tool_ranker_prefers_successful_matching_tool(self):
        ranker = ToolRanker()
        tools = [{"name": "search", "description": "search the web", "priority": 1}, {"name": "file", "description": "read files", "priority": 5}]
        history = {"search": {"success_rate": 1.0}, "file": {"success_rate": 0.0}}
        self.assertEqual(ranker.rank(tools, "search web", history)[0]["name"], "search")

    def test_tool_cache_expires_values(self):
        cache = ToolCache(default_ttl=0)
        cache.set("search", {"answer": 1})
        self.assertIsNone(cache.get("search"))

    def test_reasoning_cache_hashes_goal_and_context(self):
        cache = ReasoningCache(default_ttl=60)
        cache.set("Build API", "clean architecture", {"success": True})
        self.assertEqual(cache.get("Build API", "clean architecture"), {"success": True})
        self.assertIsNone(cache.get("Build API", "other context"))

    def test_reasoning_ranker_prefers_confident_recent_result(self):
        ranked = ReasoningRanker().rank([
            {"goal": "Build API", "confidence": 0.3, "created_at": 1},
            {"goal": "Build API", "confidence": 0.9, "created_at": time.time()},
        ], "Build API")
        self.assertEqual(ranked[0]["confidence"], 0.9)

    def test_reasoning_engine_reuses_an_explicit_safe_cache(self):
        class Executor:
            def execute(self, action):
                return {"success": True, "output": action.action}

        cache = ReasoningCache()
        engine = ReasoningEngine(action_executor=Executor(), reasoning_cache=cache)
        first = engine.run("Create calculator", "safe test")
        second = engine.run("Create calculator", "safe test")
        self.assertTrue(first["success"])
        self.assertTrue(second["cache_hit"])

    def test_reflection_score_and_report_identify_weakness(self):
        score = ReflectionScore.from_mapping({"architecture": 9, "performance": 9, "security": 3, "scalability": 9, "maintainability": 9, "testing": 9, "documentation": 9, "readability": 9})
        report = ReflectionReport(score, notes=["Avoid dynamic execution"])
        self.assertEqual(report.to_dict()["weakest_area"], "security")

    def test_learning_database_deduplicates_and_optimizer_recommends(self):
        database = LearningDatabase()
        database.record({"area": "runtime_repair", "success": False})
        database.record({"area": "runtime_repair", "success": False})
        report = LearningOptimizer(database).recommend()
        self.assertEqual(database.count(), 1)
        self.assertEqual(report["weakest_area"], "runtime_repair")

    def test_dashboard_aggregates_and_serializes_metrics(self):
        data = DashboardData().collect(projects=2, successes=1, failures=1, memory_entries=4)
        metrics = DashboardMetrics().calculate(data)
        report = DashboardReport(metrics)
        self.assertEqual(metrics["success_rate"], 0.5)
        self.assertIn("success_rate", report.to_json())

    def test_brain_layer_connects_memory_learning_and_dashboard(self):
        class Reflection:
            def scorecard(self, scores):
                return {"scores": scores}

        brain = AutonomousBrainLayer(reflection=Reflection())
        prepared = brain.prepare("Build a calculator")
        brain.record_execution("Build a calculator", True, reflection_scores={"testing": 9})
        self.assertEqual(prepared["task"].title, "Build a calculator")
        self.assertEqual(brain.dashboard()["success_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
