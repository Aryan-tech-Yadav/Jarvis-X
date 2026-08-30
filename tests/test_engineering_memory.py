import unittest

from app.engineering_memory import CodeKnowledgeBase, EngineeringMemoryGraph, ReuseEngine


class TestEngineeringMemory(unittest.TestCase):
    def test_graph_links_project_and_component(self):
        graph = EngineeringMemoryGraph()
        graph.add_node("hospital", "Hospital", "project")
        graph.add_node("auth", "Authentication", "component")
        graph.add_edge("hospital", "auth", "contains")
        self.assertEqual(graph.neighbors("hospital")[0].node_id, "auth")

    def test_code_fingerprint_is_content_addressed(self):
        base = CodeKnowledgeBase()
        first = base.index("auth.py", "token()", features=["jwt"], dependencies=["redis"])
        self.assertEqual(base.find_by_content("token()").digest, first.digest)

    def test_reuse_engine_scores_shared_features(self):
        base = CodeKnowledgeBase()
        base.index("auth.py", "token()", features=["jwt"], dependencies=["redis"])
        matches = ReuseEngine(base).find(["jwt"], ["redis"])
        self.assertEqual(matches[0].path, "auth.py")
        self.assertEqual(matches[0].score, 1.0)


if __name__ == "__main__":
    unittest.main()
