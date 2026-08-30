"""Integration test for Sprint 11 Intelligence Layer.

Tests the complete learn → reuse → improve cycle:
  1. Record project experience
  2. Store project memory
  3. Build knowledge graph
  4. Find similar projects
  5. Apply improvements
  6. Optimize prompts
  7. Verify learning persisted
"""

import os
import tempfile
import unittest

from app.intelligence.experience_engine import ExperienceEngine, ProjectExperience
from app.intelligence.project_memory import ProjectMemoryStore, ProjectMemory
from app.intelligence.knowledge_graph import KnowledgeGraph
from app.intelligence.benchmark_engine import BenchmarkEngine
from app.intelligence.self_improver import SelfImprover
from app.intelligence.similarity_engine import SimilarityEngine
from app.intelligence.engineering_memory import EngineeringMemory
from app.intelligence.pattern_library import PatternLibrary
from app.intelligence.prompt_optimizer import PromptOptimizer


class TestIntelligenceIntegration(unittest.TestCase):
    def test_learn_reuse_improve_cycle(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize all engines
            exp_engine = ExperienceEngine(experiences_path=os.path.join(tmpdir, "exp.json"))
            mem_store = ProjectMemoryStore(memory_path=os.path.join(tmpdir, "mem.json"))
            graph = KnowledgeGraph(graph_path=os.path.join(tmpdir, "graph.json"))
            bench = BenchmarkEngine(benchmarks_path=os.path.join(tmpdir, "bench.json"))
            eng_memory = EngineeringMemory(memory_path=os.path.join(tmpdir, "eng.json"))
            patterns = PatternLibrary(patterns_path=os.path.join(tmpdir, "pat.json"))
            prompts = PromptOptimizer(prompts_path=os.path.join(tmpdir, "prompts.json"))
            improver = SelfImprover(
                experience_engine=exp_engine,
                pattern_library=patterns,
                engineering_memory=eng_memory,
                benchmark_engine=bench,
            )

            # Step 1: Learn from first project
            exp1 = exp_engine.record_experience(
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
                modules=["Auth", "Billing", "Appointment"],
            )

            # Step 2: Store project memory
            memory = ProjectMemory(
                project_name="Hospital",
                version="v1",
                domain="healthcare",
                architecture={"pattern": "layered", "layers": 4},
                stack=["fastapi", "postgresql"],
                overall_score=95.0,
            )
            mem_store.store(memory)
            mem_store.add_solution("Hospital", "DB connection timeout", "Added connection pooling")

            # Step 3: Build knowledge graph
            graph.add_node("hospital", "Hospital", node_type="project")
            graph.add_node("appointment", "Appointment", node_type="module")
            graph.add_node("doctor", "Doctor", node_type="module")
            graph.add_edge("hospital", "appointment", relation="contains")
            graph.add_edge("hospital", "doctor", relation="contains")
            graph.add_edge("appointment", "doctor", relation="requires")

            # Step 4: Record engineering memories
            eng_memory.record_mistake("DB timeout", "Add connection pooling", tags=["database"])
            eng_memory.record_library("fastapi", "0.100.0", "Use for async APIs")

            # Step 5: Evaluate benchmark
            report = bench.evaluate("Hospital", {
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

            # Step 6: Find similar projects
            similarity = SimilarityEngine(experience_engine=exp_engine, memory_store=mem_store)
            similar = similarity.find_similar_projects("hospital healthcare", limit=3)
            self.assertGreater(len(similar), 0)

            # Step 7: Reuse architecture
            reused = similarity.reuse_architecture("hospital healthcare")
            self.assertIsNotNone(reused)
            self.assertEqual(reused["architecture"], "FastAPI + PostgreSQL")

            # Step 8: Analyze and improve
            improvements = improver.analyze_and_improve("Hospital", {
                "failures": [{"category": "database", "problem": "DB timeout", "fix": "Add pooling"}],
                "repair_count": 1,
                "result": "SUCCESS",
            })
            self.assertIsInstance(improvements, list)

            # Step 9: Optimize prompts
            prompts.record_prompt("backend", "Prompt v1", score=92.0)
            prompts.record_prompt("backend", "Prompt v2", score=95.0)
            best = prompts.get_best_prompt("backend")
            self.assertEqual(best.score, 95.0)

            # Step 10: Verify learning persisted
            experiences = exp_engine.get_experiences()
            self.assertEqual(len(experiences), 1)
            self.assertEqual(experiences[0].project_name, "Hospital")

            memories = mem_store.find_similar("hospital")
            self.assertGreater(len(memories), 0)

            # Verify stats work
            exp_stats = exp_engine.stats()
            self.assertEqual(exp_stats["total"], 1)

            mem_stats = mem_store.stats()
            self.assertEqual(mem_stats["total_projects"], 1)

            graph_stats = graph.stats()
            self.assertGreater(graph_stats["total_nodes"], 0)

            bench_stats = bench.history()
            self.assertGreater(len(bench_stats), 0)

            pattern_stats = patterns.stats()
            self.assertGreater(pattern_stats["total_patterns"], 0)

            prompt_stats = prompts.stats()
            self.assertEqual(prompt_stats["total_prompts"], 2)

            improvement_stats = improver.improvement_stats()
            self.assertGreaterEqual(improvement_stats["total"], 0)


if __name__ == "__main__":
    unittest.main()
