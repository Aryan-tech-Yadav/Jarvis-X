import unittest

from app.orchestrator.agent_registry import AgentRegistry
from app.orchestrator.orchestrator import Orchestrator
from app.orchestrator.task import Task


class RecordingAgent:
    def __init__(self, name, calls, success=True):
        self.name = name
        self.calls = calls
        self.success = success

    def run(self, task):
        self.calls.append((self.name, task.goal))
        return {"success": self.success, "output": self.name}


class OrchestratorApiTests(unittest.TestCase):
    def test_registry_and_task_workflow(self):
        calls = []
        registry = AgentRegistry()
        for name in ("planner", "executor", "critic", "reflection"):
            registry.register(name, RecordingAgent(name, calls))

        result = Orchestrator(registry).execute("Build API")

        self.assertTrue(result["success"])
        self.assertEqual([name for name, _ in calls], ["planner", "executor", "reflection", "critic"])
        self.assertEqual(result["task"].status, "completed")
        self.assertTrue(result["task"].created_at)

    def test_registry_lifecycle_methods(self):
        registry = AgentRegistry()
        agent = RecordingAgent("planner", [])

        registry.register("planner", agent)

        self.assertTrue(registry.exists("planner"))
        self.assertEqual(registry.list_agents(), ["planner"])
        self.assertIs(registry.unregister("planner"), agent)
        self.assertFalse(registry.exists("planner"))

    def test_agent_failure_propagates(self):
        registry = AgentRegistry()
        registry.register("planner", RecordingAgent("planner", [], success=False))

        result = Orchestrator(registry, workflow=("planner",)).execute("Build API")

        self.assertFalse(result["success"])
        self.assertEqual(result["failed_agent"], "planner")
        self.assertEqual(result["task"].status, "failed")

    def test_unknown_agent_is_reported(self):
        result = Orchestrator(AgentRegistry()).execute("Build API")

        self.assertFalse(result["success"])
        self.assertEqual(result["failed_agent"], "planner")


if __name__ == "__main__":
    unittest.main()