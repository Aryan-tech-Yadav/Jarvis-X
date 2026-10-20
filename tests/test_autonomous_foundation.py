import unittest

from app.agents.agent_context import AgentContext
from app.agents.agent_registry import AgentRegistry
from app.agents.coding_agent import CodingAgent
from app.agents.coordinator import AgentCoordinator
from app.agents.message_bus import MessageBus
from app.agents.testing_agent import TestingAgent
from app.reasoning.chain_of_thought import ChainOfThought
from app.reasoning.decision import Decision
from app.reasoning.decision_engine import DecisionEngine
from app.reasoning.dependency_graph import DependencyGraph
from app.reasoning.failure_recovery import FailureRecovery
from app.reasoning.goal_checker import GoalChecker
from app.reasoning.goal_decomposer import GoalDecomposer


class AutonomousFoundationTests(unittest.TestCase):
    def test_chain_deduplicates_and_tracks_confidence(self):
        chain = ChainOfThought()
        chain.add({"thought": "inspect", "confidence": 0.4})
        chain.add({"thought": "inspect", "confidence": 0.4})

        self.assertEqual(len(chain.history()), 1)
        self.assertEqual(chain.confidence_trend(), [0.4])

    def test_decision_engine_selects_highest_confidence(self):
        selected = DecisionEngine().choose([
            Decision("search", "find context", 0.4),
            Decision("modify", "feature missing", 0.9, "HIGH"),
        ])

        self.assertEqual(selected.tool, "modify")

    def test_goal_decomposition_and_dependency_order(self):
        steps = GoalDecomposer().decompose("Build Instagram Clone")
        graph = DependencyGraph()
        graph.add("api", ["database"])
        graph.add("database", [])

        self.assertIn("authentication", steps)
        self.assertEqual(graph.order(), ["database", "api"])

    def test_dependency_cycle_is_rejected(self):
        graph = DependencyGraph()
        graph.add("a", ["b"])
        graph.add("b", ["a"])

        with self.assertRaises(ValueError):
            graph.order()

    def test_coordinator_runs_agents_and_shares_context(self):
        registry = AgentRegistry()
        registry.register("coding", CodingAgent())
        registry.register("testing", TestingAgent())
        result = AgentCoordinator(registry, workflow=("coding", "testing")).execute("Build app")

        self.assertTrue(result["success"])
        self.assertEqual(result["context"].shared_notes.keys(), {"coding", "testing"})

    def test_coordinator_rejects_unknown_agent(self):
        result = AgentCoordinator(AgentRegistry(), workflow=("missing",)).execute("Build app")

        self.assertFalse(result["success"])
        self.assertEqual(result["agent"], "missing")

    def test_message_bus_delivery_and_empty_queue(self):
        bus = MessageBus()
        bus.send("coding", "testing", "TASK_COMPLETE", {"files": 2})
        message = bus.receive("testing")

        self.assertEqual(message.payload["files"], 2)
        self.assertIsNone(bus.receive("testing"))

    def test_goal_checker_and_failure_recovery(self):
        self.assertTrue(GoalChecker().is_complete("goal", ["api"], ["api"]))
        recovery = FailureRecovery(max_retries=2)
        self.assertEqual(recovery.decide(0, "error"), "retry")
        self.assertEqual(recovery.decide(2, "error"), "stop")


if __name__ == "__main__":
    unittest.main()