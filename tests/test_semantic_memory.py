import os
import tempfile
import unittest

from app.brain.brain_pipeline import BrainPipeline
from app.semantic_memory import SemanticMemoryManager
from app.semantic_memory.exceptions import SemanticMemoryValidationError
from app.semantic_memory.semantic_store import SemanticStore


class SemanticMemoryTests(unittest.TestCase):
    def manager(self, directory):
        return SemanticMemoryManager(SemanticStore(os.path.join(directory, "semantic.json")))

    def test_remember_persists_and_suppresses_equivalent_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = self.manager(directory)
            first = manager.remember("FastAPI JWT authentication succeeded", tags=["FastAPI", "authentication"])
            second = manager.remember("  FastAPI   JWT authentication succeeded  ", tags=["other"])
            restored = self.manager(directory)

            self.assertEqual(first.memory_id, second.memory_id)
            self.assertEqual(restored.store.get(first.memory_id).tags, ("fastapi", "authentication"))

    def test_search_combines_meaning_importance_and_confidence(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = self.manager(directory)
            manager.remember("Use SQLite for a local prototype", tags=["database"], importance=0.2)
            expected = manager.remember(
                "FastAPI JWT authentication with refresh tokens succeeded",
                tags=["fastapi", "authentication"], importance=0.9, confidence=0.95,
            )

            result = manager.search("FastAPI API authentication", limit=1)

            self.assertEqual(result[0]["id"], expected.memory_id)
            self.assertGreater(result[0]["relevance"], 0)

    def test_outcomes_relationships_statistics_and_export_are_traceable(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = self.manager(directory)
            first = manager.record_outcome("Deploy FastAPI API", True, tags=["fastapi", "deployment"])
            manager.record_outcome("FastAPI deployment rollback", False, tags=["fastapi", "deployment"])

            related = manager.related(first.memory_id)
            exported = manager.export()

            self.assertEqual(related[0]["relationship"], "shared_tags")
            self.assertEqual(exported["statistics"]["by_type"], {"failure": 1, "success": 1})
            self.assertTrue(exported["memories"])

    def test_invalid_values_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = self.manager(directory)
            with self.assertRaises(SemanticMemoryValidationError):
                manager.remember("", importance=0.5)
            with self.assertRaises(SemanticMemoryValidationError):
                manager.remember("valid", confidence=1.1)
            with self.assertRaises(SemanticMemoryValidationError):
                manager.remember("valid", tags=[3])

    def test_brain_pipeline_includes_read_only_semantic_context(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = self.manager(directory)
            stored = memory.remember(
                "FastAPI authentication used JWT successfully",
                tags=["fastapi", "authentication"], importance=0.9,
            )

            brief = BrainPipeline(semantic_memory=memory).prepare("Build a FastAPI app with login")

            self.assertIn("semantic_context", brief)
            self.assertEqual(brief["semantic_context"][0]["id"], stored.memory_id)
            self.assertEqual(len(memory.store.all()), 1)


if __name__ == "__main__":
    unittest.main()
