"""Tests for Sprint 11 Intelligence Layer."""

import os
import tempfile
import unittest

from app.intelligence.experience_engine import ExperienceEngine, ProjectExperience
from app.intelligence.project_memory import ProjectMemoryStore, ProjectMemory
from app.intelligence.knowledge_graph import KnowledgeGraph, GraphNode, GraphEdge
from app.intelligence.benchmark_engine import BenchmarkEngine, BenchmarkReport
from app.intelligence.self_improver import SelfImprover, Improvement
from app.intelligence.similarity_engine import SimilarityEngine, SimilarityResult
from app.intelligence.engineering_memory import EngineeringMemory, EngineeringMemoryEntry
from app.intelligence.pattern_library import PatternLibrary, EngineeringPattern
from app.intelligence.prompt_optimizer import PromptOptimizer, PromptVersion


class TestExperienceEngine(unittest.TestCase):
    def test_record_and_retrieve(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ExperienceEngine(experiences_path=os.path.join(tmpdir, "exp.json"))
            exp = engine.record_experience(
                project_name="Hospital",
                execution_time_sec=120.0,
                planning_score=96.0,
                execution_score=94.0,
                quality_score=95.0,
                repair_count=1,
                test_coverage=92.0,
                domain="healthcare",
                architecture="FastAPI + PostgreSQL",
                stack=["fastapi", "postgresql", "redis"],
            )
            self.assertEqual(exp.project_name, "Hospital")
            self.assertEqual(exp.domain, "healthcare")
            self.assertAlmostEqual(exp.overall_score, 95.0)

            experiences = engine.get_experiences()
            self.assertEqual(len(experiences), 1)

    def test_search_similar(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ExperienceEngine(experiences_path=os.path.join(tmpdir, "exp.json"))
            engine.record_experience("Hospital", domain="healthcare", architecture="FastAPI")
            engine.record_experience("CRM", domain="business", architecture="Django")
            similar = engine.search_similar("healthcare hospital")
            self.assertEqual(len(similar), 1)
            self.assertEqual(similar[0].project_name, "Hospital")

    def test_stats(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ExperienceEngine(experiences_path=os.path.join(tmpdir, "exp.json"))
            engine.record_experience("Hospital", result="SUCCESS")
            engine.record_experience("CRM", result="FAILED")
            stats = engine.stats()
            self.assertEqual(stats["total"], 2)
            self.assertEqual(stats["success_rate"], 0.5)


class TestProjectMemory(unittest.TestCase):
    def test_store_and_retrieve(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ProjectMemoryStore(memory_path=os.path.join(tmpdir, "mem.json"))
            memory = ProjectMemory(
                project_name="Hospital",
                version="v1",
                domain="healthcare",
                architecture={"pattern": "layered", "layers": 4},
                stack=["fastapi", "postgresql"],
            )
            key = store.store(memory)
            self.assertIn("Hospital", key)

            retrieved = store.get("Hospital", "v1")
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.domain, "healthcare")

    def test_find_similar(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ProjectMemoryStore(memory_path=os.path.join(tmpdir, "mem.json"))
            store.store(ProjectMemory(project_name="Hospital", domain="healthcare", stack=["fastapi"]))
            store.store(ProjectMemory(project_name="CRM", domain="business", stack=["django"]))
            similar = store.find_similar("hospital management", limit=2)
            self.assertEqual(len(similar), 1)
            self.assertEqual(similar[0].project_name, "Hospital")

    def test_add_solution(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ProjectMemoryStore(memory_path=os.path.join(tmpdir, "mem.json"))
            store.add_solution("Hospital", "DB connection fails", "Add retry logic")
            memory = store.get("Hospital", "v1")
            self.assertEqual(len(memory.problems), 1)
            self.assertEqual(len(memory.solutions), 1)


class TestKnowledgeGraph(unittest.TestCase):
    def test_add_nodes_and_edges(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            graph = KnowledgeGraph(graph_path=os.path.join(tmpdir, "graph.json"))
            graph.add_node("hospital", "Hospital", node_type="project")
            graph.add_node("appointment", "Appointment", node_type="module")
            graph.add_node("doctor", "Doctor", node_type="module")
            graph.add_edge("hospital", "appointment", relation="contains")
            graph.add_edge("hospital", "doctor", relation="contains")

            neighbors = graph.get_neighbors("hospital")
            self.assertEqual(len(neighbors), 2)

    def test_shortest_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            graph = KnowledgeGraph(graph_path=os.path.join(tmpdir, "graph.json"))
            graph.add_node("a", "A")
            graph.add_node("b", "B")
            graph.add_node("c", "C")
            graph.add_edge("a", "b", relation="links")
            graph.add_edge("b", "c", relation="links")
            path = graph.find_shortest_path("a", "c")
            self.assertEqual(path, ["a", "b", "c"])

    def test_similarity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            graph = KnowledgeGraph(graph_path=os.path.join(tmpdir, "graph.json"))
            graph.add_node("a", "A")
            graph.add_node("b", "B")
            graph.add_node("c", "C")
            graph.add_edge("a", "b", relation="links")
            graph.add_edge("a", "c", relation="links")
            graph.add_edge("b", "c", relation="links")
            similar = graph.similarity("a")
            self.assertEqual(len(similar), 2)


class TestBenchmarkEngine(unittest.TestCase):
    def test_evaluate_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = BenchmarkEngine(benchmarks_path=os.path.join(tmpdir, "bench.json"))
            report = engine.evaluate("Hospital", {
                "planning_score": 96.0,
                "architecture_score": 95.0,
                "execution_score": 94.0,
                "quality_score": 95.0,
                "test_coverage": 92.0,
                "security_score": 90.0,
                "performance_score": 88.0,
                "repair_count": 1,
                "documentation_complete": True,
                "deployment_ready": True,
            })
            self.assertEqual(report.project_name, "Hospital")
            self.assertGreater(report.overall_score, 80.0)
            self.assertIn(report.grade, ["A", "B", "C", "D", "F"])

    def test_grade_thresholds(self):
        engine = BenchmarkEngine()
        self.assertEqual(engine._grade(95), "A")
        self.assertEqual(engine._grade(85), "B")
        self.assertEqual(engine._grade(75), "C")
        self.assertEqual(engine._grade(65), "D")
        self.assertEqual(engine._grade(50), "F")


class TestSelfImprover(unittest.TestCase):
    def test_analyze_and_improve(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            improver = SelfImprover(
                experience_engine=ExperienceEngine(experiences_path=os.path.join(tmpdir, "exp.json")),
                pattern_library=PatternLibrary(patterns_path=os.path.join(tmpdir, "pat.json")),
                engineering_memory=EngineeringMemory(memory_path=os.path.join(tmpdir, "eng.json")),
                benchmark_engine=BenchmarkEngine(benchmarks_path=os.path.join(tmpdir, "bench.json")),
            )
            metrics = {
                "failures": [{"category": "auth", "problem": "Token expired", "fix": "Add refresh"}],
                "repair_count": 5,
                "result": "SUCCESS",
            }
            improvements = improver.analyze_and_improve("Hospital", metrics)
            self.assertIsInstance(improvements, list)

    def test_improvement_stats(self):
        improver = SelfImprover()
        improver._improvements.append(Improvement(category="auth", description="test", delta=5.0))
        stats = improver.improvement_stats()
        self.assertEqual(stats["total"], 1)


class TestSimilarityEngine(unittest.TestCase):
    def test_find_similar_projects(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exp_engine = ExperienceEngine(experiences_path=os.path.join(tmpdir, "exp.json"))
            mem_store = ProjectMemoryStore(memory_path=os.path.join(tmpdir, "mem.json"))
            exp_engine.record_experience("Hospital", domain="healthcare", architecture="FastAPI")
            mem_store.store(ProjectMemory(project_name="Hospital", domain="healthcare", stack=["fastapi"]))

            engine = SimilarityEngine(experience_engine=exp_engine, memory_store=mem_store)
            similar = engine.find_similar_projects("hospital management", limit=5)
            self.assertGreater(len(similar), 0)
            self.assertGreater(similar[0].similarity_score, 0.0)

    def test_reuse_architecture(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exp_engine = ExperienceEngine(experiences_path=os.path.join(tmpdir, "exp.json"))
            exp_engine.record_experience("Hospital", architecture="FastAPI + PostgreSQL", stack=["fastapi"])
            engine = SimilarityEngine(experience_engine=exp_engine)
            arch = engine.reuse_architecture("hospital")
            self.assertIsNotNone(arch)
            self.assertEqual(arch["architecture"], "FastAPI + PostgreSQL")


class TestEngineeringMemory(unittest.TestCase):
    def test_record_mistake(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = EngineeringMemory(memory_path=os.path.join(tmpdir, "eng.json"))
            entry = mem.record_mistake("DB connection fails", "Add retry logic")
            self.assertEqual(entry.category, "mistake")
            self.assertIn("Fix:", entry.description)

    def test_record_library(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = EngineeringMemory(memory_path=os.path.join(tmpdir, "eng.json"))
            entry = mem.record_library("fastapi", "0.100.0", "Use for async APIs")
            self.assertEqual(entry.category, "library")
            self.assertEqual(entry.context["library"], "fastapi")

    def test_search(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = EngineeringMemory(memory_path=os.path.join(tmpdir, "eng.json"))
            mem.record_mistake("Auth fails", "Add JWT refresh", tags=["auth"])
            results = mem.search("auth")
            self.assertEqual(len(results), 1)

    def test_stats(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = EngineeringMemory(memory_path=os.path.join(tmpdir, "eng.json"))
            mem.record_mistake("x", "y")
            mem.record_library("z", "1.0")
            stats = mem.stats()
            self.assertEqual(stats["total_entries"], 2)


class TestPatternLibrary(unittest.TestCase):
    def test_seeded_patterns(self):
        library = PatternLibrary(patterns_path=":memory:")
        patterns = library.find_patterns(category="auth")
        self.assertGreater(len(patterns), 0)
        self.assertEqual(patterns[0].name, "JWT Authentication")

    def test_add_and_find_pattern(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            library = PatternLibrary(patterns_path=os.path.join(tmpdir, "pat.json"))
            pattern = EngineeringPattern(
                name="Custom Pattern",
                category="api",
                description="A custom pattern",
                code_template="code",
                language="python",
                tags=["custom"],
            )
            library.add_pattern(pattern)
            found = library.find_patterns(category="api", tags=["custom"])
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0].name, "Custom Pattern")

    def test_record_usage(self):
        library = PatternLibrary(patterns_path=":memory:")
        patterns = library.find_patterns(category="auth")
        pattern = patterns[0]
        initial_usage = pattern.usage_count
        library.record_usage(pattern.pattern_id, success=True)
        self.assertEqual(pattern.usage_count, initial_usage + 1)

    def test_stats(self):
        library = PatternLibrary(patterns_path=":memory:")
        stats = library.stats()
        self.assertGreater(stats["total_patterns"], 0)


class TestPromptOptimizer(unittest.TestCase):
    def test_record_and_get_best(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            optimizer = PromptOptimizer(prompts_path=os.path.join(tmpdir, "prompts.json"))
            pv1 = optimizer.record_prompt("backend", "Prompt v1", score=92.0)
            pv2 = optimizer.record_prompt("backend", "Prompt v2", score=95.0)
            best = optimizer.get_best_prompt("backend")
            self.assertIsNotNone(best)
            self.assertEqual(best.score, 95.0)
            self.assertEqual(best.version, 2)

    def test_active_prompt(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            optimizer = PromptOptimizer(prompts_path=os.path.join(tmpdir, "prompts.json"))
            optimizer.record_prompt("backend", "Prompt v1", score=90.0)
            active = optimizer.get_active_prompt("backend")
            self.assertIsNotNone(active)
            self.assertTrue(active.is_active)

    def test_promote_to_active(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            optimizer = PromptOptimizer(prompts_path=os.path.join(tmpdir, "prompts.json"))
            pv1 = optimizer.record_prompt("backend", "Prompt v1", score=90.0)
            pv2 = optimizer.record_prompt("backend", "Prompt v2", score=95.0)
            optimizer.promote_to_active("backend", pv2.prompt_id)
            active = optimizer.get_active_prompt("backend")
            self.assertEqual(active.prompt_id, pv2.prompt_id)

    def test_stats(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            optimizer = PromptOptimizer(prompts_path=os.path.join(tmpdir, "prompts.json"))
            optimizer.record_prompt("backend", "Prompt 1", score=90.0)
            optimizer.record_prompt("frontend", "Prompt 2", score=85.0)
            stats = optimizer.stats()
            self.assertEqual(stats["total_agents"], 2)
            self.assertEqual(stats["total_prompts"], 2)


if __name__ == "__main__":
    unittest.main()
