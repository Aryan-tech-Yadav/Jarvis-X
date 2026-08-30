import time
import unittest

from app.autonomy.brain_layer import AutonomousBrainLayer
from app.dashboard.dashboard_data import DashboardData
from app.dashboard.dashboard_export import DashboardExport
from app.dashboard.dashboard_metrics import DashboardMetrics
from app.dashboard.dashboard_report import DashboardReport
from app.knowledge.knowledge_base import KnowledgeBase
from app.learning.learning_database import LearningDatabase
from app.learning.learning_optimizer import LearningOptimizer
from app.learning.learning_report import LearningReport
from app.learning.learning_score import LearningScore
from app.memory.memory_cleaner import MemoryCleaner
from app.memory.memory_compressor import MemoryCompressor
from app.memory.memory_index import MemoryIndex
from app.memory.memory_ranker import MemoryRanker
from app.memory.memory_search import MemorySearch
from app.reasoning.reasoning_cache import ReasoningCache
from app.reasoning.reasoning_history import ReasoningHistory
from app.reasoning.reasoning_ranker import ReasoningRanker
from app.reflection.reflection_metrics import ReflectionMetrics
from app.reflection.reflection_report import ReflectionReport
from app.reflection.reflection_score import ReflectionScore
from app.task.task import AutonomousTask
from app.task.task_graph import TaskGraph
from app.task.task_optimizer import TaskOptimizer
from app.task.task_scheduler import TaskScheduler
from app.tools.tool_cache import ToolCache
from app.tools.tool_history import ToolCall, ToolHistory
from app.tools.tool_ranker import ToolRanker


class MemoryEdgeTests(unittest.TestCase):
    def test_index_returns_keyword_candidates(self):
        index = MemoryIndex()
        item = index.add("Cache a python result")
        self.assertEqual(index.candidates("python")[0]["id"], item["id"])

    def test_index_remove_removes_entry(self):
        index = MemoryIndex()
        item = index.add("temporary memory")
        self.assertTrue(index.remove(item["id"]))
        self.assertEqual(index.entries(), [])

    def test_ranker_uses_importance_when_words_tie(self):
        now = time.time()
        low = {"content": "python cache", "importance": 0, "priority": 0, "created_at": now}
        high = {"content": "python cache", "importance": 1, "priority": 0, "created_at": now}
        self.assertIs(MemoryRanker().rank([low, high], "python")[0], high)

    def test_empty_memory_search_returns_nothing(self):
        self.assertEqual(MemorySearch(MemoryIndex()).search(""), [])

    def test_compressor_leaves_short_history_unchanged(self):
        entries = [{"content": "one"}]
        self.assertFalse(MemoryCompressor(max_entries=2).compress(entries)["compressed"])

    def test_cleaner_enforces_entry_limit(self):
        cleaned = MemoryCleaner(max_entries=1).clean([
            {"content": "a", "priority": 1}, {"content": "b", "priority": 2},
        ])
        self.assertEqual(cleaned[0]["content"], "b")


class KnowledgeEdgeTests(unittest.TestCase):
    def test_duplicate_fact_returns_same_identifier(self):
        base = KnowledgeBase()
        self.assertEqual(base.add_fact("Python is typed")["id"], base.add_fact("Python is typed")["id"])

    def test_knowledge_search_honours_limit(self):
        base = KnowledgeBase()
        base.add_fact("Python one", topics=["python"])
        base.add_fact("Python two", topics=["python"])
        self.assertEqual(len(base.search("python", limit=1)), 1)

    def test_related_unknown_fact_is_empty(self):
        self.assertEqual(KnowledgeBase().related("missing"), [])

    def test_fact_extraction_splits_sentences(self):
        self.assertEqual(len(KnowledgeBase().extract_facts("One fact. Two fact.")), 2)

    def test_category_is_searchable(self):
        base = KnowledgeBase()
        base.add_fact("Unit tests validate code", category="testing")
        self.assertEqual(base.search("testing")[0]["category"], "testing")


class TaskEdgeTests(unittest.TestCase):
    def test_levels_expose_parallel_work(self):
        graph = TaskGraph()
        graph.add(AutonomousTask("a", task_id="a"))
        graph.add(AutonomousTask("b", task_id="b"))
        self.assertEqual(set(graph.levels()[0]), {"a", "b"})

    def test_scheduler_orders_higher_priority_first(self):
        scheduler = TaskScheduler()
        scheduler.submit(AutonomousTask("low", task_id="low", priority=1))
        scheduler.submit(AutonomousTask("high", task_id="high", priority=2))
        self.assertEqual(scheduler.next_batch()[0].task_id, "high")

    def test_scheduler_marks_exhausted_task_failed(self):
        scheduler = TaskScheduler()
        scheduler.submit(AutonomousTask("build", task_id="build", max_retries=0))
        self.assertEqual(scheduler.fail("build").status, "failed")

    def test_scheduler_resume_returns_interrupted_task(self):
        scheduler = TaskScheduler()
        scheduler.submit(AutonomousTask("build", task_id="build"))
        scheduler.next_batch()
        self.assertEqual(scheduler.resume()[0].task_id, "build")

    def test_optimizer_estimates_parallel_tasks_once(self):
        tasks = [AutonomousTask("a", eta_seconds=3), AutonomousTask("b", eta_seconds=5)]
        self.assertEqual(TaskOptimizer().estimate(tasks), 5)


class ToolEdgeTests(unittest.TestCase):
    def test_tool_history_calculates_success_rate(self):
        history = ToolHistory()
        history.record(ToolCall("search", 0, True))
        history.record(ToolCall("search", 0, False))
        self.assertEqual(history.statistics()["search"]["success_rate"], 0.5)

    def test_tool_cache_clear_removes_value(self):
        cache = ToolCache()
        cache.set("x", 1)
        cache.clear()
        self.assertIsNone(cache.get("x"))

    def test_tool_ranker_uses_priority_for_equal_matches(self):
        tools = [{"name": "a", "description": "search", "priority": 1}, {"name": "b", "description": "search", "priority": 2}]
        self.assertEqual(ToolRanker().rank(tools, "search")[0]["name"], "b")

    def test_tool_ranker_handles_object_tools(self):
        class Tool:
            name, description, priority = "search", "web search", 1
        self.assertEqual(ToolRanker().rank([Tool()], "web")[0].name, "search")

    def test_tool_cache_returns_unexpired_value(self):
        cache = ToolCache(default_ttl=10)
        cache.set("x", {"answer": 1})
        self.assertEqual(cache.get("x")["answer"], 1)


class ReasoningEdgeTests(unittest.TestCase):
    def test_reasoning_cache_expires(self):
        cache = ReasoningCache(default_ttl=0)
        cache.set("goal", "", {"success": True})
        self.assertIsNone(cache.get("goal"))

    def test_reasoning_history_finds_matching_goal(self):
        history = ReasoningHistory()
        history.record("Build API", {"success": True})
        self.assertEqual(history.search("api")[0]["goal"], "Build API")

    def test_reasoning_ranker_honours_limit(self):
        values = [{"goal": "api", "confidence": 1}, {"goal": "api", "confidence": 0.5}]
        self.assertEqual(len(ReasoningRanker().rank(values, "api", limit=1)), 1)

    def test_reasoning_cache_copies_results(self):
        cache = ReasoningCache()
        result = {"items": []}
        cache.set("goal", "", result)
        cache.get("goal")["items"].append("mutated")
        self.assertEqual(cache.get("goal")["items"], [])

    def test_reasoning_history_empty_query_has_no_matches(self):
        history = ReasoningHistory()
        history.record("Build API", {})
        self.assertEqual(history.search("unrelated"), [])


class ReflectionLearningDashboardEdgeTests(unittest.TestCase):
    def test_reflection_scores_are_clamped(self):
        score = ReflectionScore.from_mapping({"security": 99})
        self.assertEqual(score.scores["security"], 10)

    def test_reflection_metrics_averages_reports(self):
        metrics = ReflectionMetrics()
        metrics.record(ReflectionReport(ReflectionScore.from_mapping({"testing": 4})))
        metrics.record(ReflectionReport(ReflectionScore.from_mapping({"testing": 6})))
        self.assertEqual(metrics.averages()["testing"], 5)

    def test_reflection_report_serializes(self):
        self.assertIn("weakest_area", ReflectionReport(ReflectionScore()).to_json())

    def test_learning_database_rejects_missing_area(self):
        with self.assertRaises(ValueError):
            LearningDatabase().record({"success": True})

    def test_learning_database_groups_areas(self):
        database = LearningDatabase()
        database.record({"area": "tools", "success": True})
        self.assertEqual(len(database.by_area()["tools"]), 1)

    def test_learning_score_of_empty_outcomes_is_neutral(self):
        self.assertEqual(LearningScore().score([]), 1.0)

    def test_learning_optimizer_handles_empty_database(self):
        self.assertIsNone(LearningOptimizer(LearningDatabase()).recommend()["weakest_area"])

    def test_learning_report_serializes_recommendation(self):
        self.assertIn("recommendation", LearningReport({"recommendation": "test"}).to_json())

    def test_dashboard_metrics_calculates_repair_rate(self):
        result = DashboardMetrics().calculate(DashboardData().collect(projects=2, repairs=1))
        self.assertEqual(result["repair_rate"], 0.5)

    def test_dashboard_report_has_markdown(self):
        self.assertIn("Jarvis-X", DashboardReport({"projects": 1}).to_markdown())

    def test_dashboard_export_generates_csv(self):
        self.assertIn("metric", DashboardExport().csv({"projects": 1}))

    def test_dashboard_data_supplies_zero_defaults(self):
        self.assertEqual(DashboardData().collect()["tool_calls"], 0)

    def test_brain_layer_records_failed_execution(self):
        class Reflection:
            def scorecard(self, scores): return scores
        brain = AutonomousBrainLayer(reflection=Reflection())
        brain.record_execution("broken task", False)
        self.assertEqual(brain.dashboard()["failures"], 1)


if __name__ == "__main__":
    unittest.main()
