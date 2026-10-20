import unittest

from app.agents.agent_registry import AgentRegistry
from app.orchestrator.multi_agent_orchestrator import MultiAgentOrchestrator
from app.orchestrator.shared_context import SharedContext


class FakeAgent:
    def __init__(self, name, responses, calls):
        self.name = name
        self.responses = iter(responses)
        self.calls = calls

    def run(self, context):
        self.calls.append((self.name, context))
        return next(self.responses)


def registry_for(responses, calls):
    registry = AgentRegistry()
    for name, agent_responses in responses.items():
        registry.register(name, FakeAgent(name, agent_responses, calls))
    return registry


class MultiAgentOrchestratorTests(unittest.TestCase):
    def test_default_pipeline_shares_context_and_completes(self):
        calls = []
        responses = {
            name: [{"success": True, "output": name}]
            for name in ("researcher", "planner", "analyzer", "coder", "reviewer", "critic", "validator")
        }
        registry = registry_for(responses, calls)
        result = MultiAgentOrchestrator(registry=registry).run("Build app")

        self.assertTrue(result["success"])
        self.assertEqual([name for name, _ in calls], list(responses))
        self.assertIsInstance(result["context"], SharedContext)
        self.assertEqual(len(result["context"].progress), 7)

    def test_failed_validation_repairs_then_rechecks_and_reviews(self):
        calls = []
        responses = {
            "researcher": [{"success": True, "output": "research"}],
            "planner": [{"success": True, "output": "plan"}],
            "analyzer": [{"success": True, "output": "analysis"}],
            "coder": [{"success": True, "output": "coded"}],
            "reviewer": [{"success": True, "output": "review"}, {"success": True, "output": "reviewed"}],
            "critic": [{"success": True, "output": "critic"}, {"success": True, "output": "critic"}],
            "validator": [
                {"success": False, "output": "missing file"},
                {"success": True, "output": "valid"},
                {"success": True, "output": "valid"},
            ],
            "repair": [{"success": True, "output": ["main.py"]}],
        }
        result = MultiAgentOrchestrator(
            registry=registry_for(responses, calls), max_repairs=1
        ).run("Build app")

        self.assertTrue(result["success"])
        self.assertEqual(
            [name for name, _ in calls],
            ["researcher", "planner", "analyzer", "coder", "reviewer", "critic", "validator",
             "repair", "validator", "reviewer", "critic", "validator"],
        )

    def test_missing_agent_returns_structured_failure(self):
        registry = AgentRegistry()
        result = MultiAgentOrchestrator(registry=registry).run("Build app")

        self.assertFalse(result["success"])
        self.assertEqual(result["failed_agent"], "researcher")


if __name__ == "__main__":
    unittest.main()