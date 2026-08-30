import unittest

from app.kernel.execution_graph import ExecutionGraph


class ExecutionGraphTests(unittest.TestCase):
    def test_ready_orders_independent_nodes_by_priority_then_id(self):
        graph = ExecutionGraph()
        graph.add_node("docs", priority=1)
        graph.add_node("security", priority=3)
        graph.add_node("tests", priority=1)
        graph.add_node("release", priority=10)
        graph.add_dependency("release", "security")

        self.assertEqual(
            [node["id"] for node in graph.ready()],
            ["security", "docs", "tests"],
        )
        self.assertEqual(
            [node["id"] for node in graph.ready({"security"})],
            ["release", "docs", "tests"],
        )

    def test_levels_express_parallel_work_and_are_deterministic(self):
        graph = ExecutionGraph()
        for node_id, priority in (("test", 0), ("frontend", 1), ("backend", 2), ("design", 0)):
            graph.add_node(node_id, priority=priority)
        graph.add_dependency("frontend", "design")
        graph.add_dependency("backend", "design")
        graph.add_dependency("test", "frontend")
        graph.add_dependency("test", "backend")

        self.assertEqual(
            graph.levels(),
            [["design"], ["backend", "frontend"], ["test"]],
        )

    def test_dependents_and_critical_path(self):
        graph = ExecutionGraph()
        for node_id in ("requirements", "architecture", "backend", "frontend", "qa"):
            graph.add_node(node_id)
        graph.add_dependency("architecture", "requirements")
        graph.add_dependency("backend", "architecture")
        graph.add_dependency("frontend", "architecture")
        graph.add_dependency("qa", "backend")
        graph.add_dependency("qa", "frontend")

        self.assertEqual(graph.dependents("architecture"), ["backend", "frontend"])
        self.assertEqual(
            graph.critical_path(),
            ["requirements", "architecture", "backend", "qa"],
        )

    def test_unknown_nodes_and_cycles_are_rejected_without_corrupting_graph(self):
        graph = ExecutionGraph()
        graph.add_node("plan")
        graph.add_node("build")
        graph.add_dependency("build", "plan")

        with self.assertRaisesRegex(ValueError, "Unknown execution node"):
            graph.add_dependency("build", "missing")
        with self.assertRaisesRegex(ValueError, "would create a cycle"):
            graph.add_dependency("plan", "build")
        with self.assertRaisesRegex(ValueError, "Unknown completed"):
            graph.ready({"missing"})

        self.assertEqual(graph.levels(), [["plan"], ["build"]])

    def test_duplicate_and_invalid_nodes_are_rejected(self):
        graph = ExecutionGraph()
        graph.add_node("plan", payload={"goal": "notes"}, priority=2)

        node = graph.get_node("plan")
        self.assertEqual(node, {"id": "plan", "payload": {"goal": "notes"}, "priority": 2})
        node["payload"]["goal"] = "mutated"
        self.assertEqual(graph.get_node("plan")["payload"], {"goal": "notes"})
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            graph.add_node("plan")
        with self.assertRaisesRegex(ValueError, "non-empty"):
            graph.add_node("")
        with self.assertRaisesRegex(TypeError, "integer"):
            graph.add_node("invalid-priority", priority=1.5)


if __name__ == "__main__":
    unittest.main()
