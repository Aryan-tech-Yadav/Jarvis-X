import os
import tempfile
import unittest

from app.agents.research_agent import ResearchAgent
from app.knowledge.knowledge_manager import KnowledgeManager
from app.knowledge.vector_store import VectorStore
from app.orchestrator.shared_context import SharedContext


class FakeInternet:
    def __init__(self):
        self.calls = 0

    def search_and_summarize(self, query):
        self.calls += 1
        return f"{query} uses a stable application programming interface."


class KnowledgeTests(unittest.TestCase):
    def test_add_search_and_duplicate_suppression(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = KnowledgeManager(VectorStore(os.path.join(directory, "knowledge.json")))
            first = manager.add_document("Python decorators wrap functions", {"source": "notes"})
            second = manager.add_document("Python decorators wrap functions")

            self.assertEqual(first, second)
            self.assertEqual(manager.search("decorators functions")[0]["id"], first)

    def test_persistence_survives_new_manager(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "knowledge.json")
            KnowledgeManager(VectorStore(path)).add_document("Cosine similarity ranks documents")
            restored = KnowledgeManager(VectorStore(path))

            self.assertEqual(restored.retrieve_similar("similarity documents")[0]["text"], "Cosine similarity ranks documents")

    def test_research_uses_existing_knowledge_before_web(self):
        with tempfile.TemporaryDirectory() as directory:
            knowledge = KnowledgeManager(VectorStore(os.path.join(directory, "knowledge.json")))
            knowledge.add_document("FastAPI exposes Python web APIs")
            internet = FakeInternet()
            context = SharedContext("Python web APIs")

            result = ResearchAgent(knowledge, internet).run(context)

            self.assertTrue(result["success"])
            self.assertEqual(result["output"]["source"], "knowledge_base")
            self.assertEqual(internet.calls, 0)

    def test_research_saves_missing_knowledge(self):
        with tempfile.TemporaryDirectory() as directory:
            knowledge = KnowledgeManager(VectorStore(os.path.join(directory, "knowledge.json")))
            internet = FakeInternet()
            context = SharedContext("Unknown library")

            result = ResearchAgent(knowledge, internet).run(context)

            self.assertTrue(result["success"])
            self.assertEqual(internet.calls, 1)
            self.assertEqual(knowledge.search("Unknown library")[0]["metadata"]["source"], "web_research")

    def test_reindex_replaces_previous_project_documents(self):
        with tempfile.TemporaryDirectory() as directory:
            project = os.path.join(directory, "project")
            os.makedirs(project)
            file_path = os.path.join(project, "README.md")
            with open(file_path, "w", encoding="utf-8") as file:
                file.write("Old authentication approach")
            knowledge = KnowledgeManager(VectorStore(os.path.join(directory, "knowledge.json")))
            knowledge.index_project(project)

            with open(file_path, "w", encoding="utf-8") as file:
                file.write("New payment approach")
            knowledge.index_project(project)

            texts = [item["text"] for item in knowledge.search("approach", limit=10)]
            self.assertEqual(texts.count("New payment approach"), 1)
            self.assertNotIn("Old authentication approach", texts)

    def test_unchanged_project_file_is_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            project = os.path.join(directory, "project")
            os.makedirs(project)
            with open(os.path.join(project, "README.md"), "w", encoding="utf-8") as file:
                file.write("Stable documentation")
            knowledge = KnowledgeManager(VectorStore(os.path.join(directory, "knowledge.json")))

            first = knowledge.index_project(project)
            second = knowledge.index_project(project)

            self.assertEqual(len(first), 1)
            self.assertEqual(second, [])


if __name__ == "__main__":
    unittest.main()