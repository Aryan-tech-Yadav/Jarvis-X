import os
import tempfile
import unittest

from app.learning.experience_manager import ExperienceManager
from app.learning.learning_engine import LearningEngine
from app.learning.learning_memory import LearningMemory
from app.learning.lesson_store import LessonStore
from app.learning.code_pattern import CodePattern
from app.learning.ranking import PatternRanking
from app.orchestrator.shared_context import SharedContext


class LearningTests(unittest.TestCase):
    def test_successful_task_is_extracted_and_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ExperienceManager(os.path.join(directory, "experiences.json"))
            context = SharedContext("Build a calculator")
            context.progress.append({"agent": "planner"})
            context.validation = {"output": "Project validation passed"}

            result = LearningEngine(manager).learn(context)

            self.assertTrue(result["success"])
            self.assertTrue(result["learned"])
            self.assertEqual(len(manager.get_experiences()), 1)

    def test_duplicate_successful_task_is_not_stored_twice(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ExperienceManager(os.path.join(directory, "experiences.json"))
            engine = LearningEngine(manager)
            context = SharedContext("Build a calculator")

            first = engine.learn(context)
            second = engine.learn(context)

            self.assertTrue(first["learned"])
            self.assertFalse(second["learned"])
            self.assertEqual(len(manager.get_experiences()), 1)

    def test_failed_task_is_not_learned(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ExperienceManager(os.path.join(directory, "experiences.json"))
            result = LearningEngine(manager).learn(SharedContext("Broken task"), success=False)

            self.assertFalse(result["success"])
            self.assertEqual(manager.get_experiences(), [])

    def test_experiences_can_be_recalled_by_goal(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ExperienceManager(os.path.join(directory, "experiences.json"))
            manager.save_experience({"goal": "Build a calculator", "summary": "Use small modules"})

            matches = manager.search("calculator")

            self.assertEqual(matches[0]["goal"], "Build a calculator")

    def test_duplicate_lessons_merge_occurrences(self):
        with tempfile.TemporaryDirectory() as directory:
            store = LessonStore(os.path.join(directory, "lessons.json"))
            memory = LearningMemory(store)

            self.assertTrue(memory.remember("Use small modules", "structure"))
            self.assertFalse(memory.remember("Use small modules", "structure"))
            self.assertEqual(store.get_lessons()[0]["occurrences"], 2)

    def test_learning_engine_stores_a_reusable_lesson(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ExperienceManager(os.path.join(directory, "experiences.json"))
            memory = LearningMemory(LessonStore(os.path.join(directory, "lessons.json")))

            result = LearningEngine(manager, learning_memory=memory).learn(SharedContext("Build API"))

            self.assertTrue(result["success"])
            self.assertTrue(result["lesson_saved"])
            self.assertEqual(len(memory.recall("small modules")), 0)

    def test_patterns_are_ranked_for_reuse(self):
        patterns = [
            CodePattern("api", "FastAPI route", tags=["api"]),
            CodePattern("cli", "argparse command", tags=["cli"]),
        ]

        ranked = PatternRanking().rank(patterns, "api")

        self.assertEqual(ranked[0].name, "api")


if __name__ == "__main__":
    unittest.main()