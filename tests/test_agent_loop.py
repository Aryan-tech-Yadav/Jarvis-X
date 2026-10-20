import unittest

from app.agent_loop.agent_loop import AgentLoop
from app.agent_loop.agent_state import AgentState
from app.agent_loop.observation_manager import ObservationManager
from app.reasoning.action import Action
from app.reasoning.confidence_router import ConfidenceRouter
from app.reasoning.error_classifier import ReasoningErrorClassifier
from app.reasoning.failure_recovery import FailureRecovery
from app.reasoning.retry_strategy import RetryStrategy
from app.reasoning.thought import Thought


class FakeThinker:
    def __init__(self, thoughts):
        self.thoughts = iter(thoughts)

    def generate(self, state):
        return next(self.thoughts)


class FakeExecutor:
    def __init__(self, results):
        self.results = iter(results)

    def execute(self, action):
        return next(self.results)


class AgentLoopTests(unittest.TestCase):
    def test_state_serialization(self):
        state = AgentState(goal="Build", plan=["code"])
        restored = AgentState.from_dict(state.to_dict())
        self.assertEqual(restored.goal, "Build")
        self.assertEqual(restored.plan, ["code"])

    def test_loop_finishes_after_successful_thought(self):
        thought = Thought(text="write", tool="file", action="write", finished=True)
        result = AgentLoop(FakeThinker([thought]), FakeExecutor([{"success": True, "output": "done"}])).run("Build")
        self.assertTrue(result["success"])
        self.assertEqual(len(result["state"]["history"]), 1)

    def test_loop_stops_after_retry_limit(self):
        thought = Thought(text="retry", tool="file", action="read", finished=False)
        result = AgentLoop(FakeThinker([thought, thought, thought]), FakeExecutor([{"success": False}] * 3), max_retries=2).run("Build")
        self.assertFalse(result["success"])
        self.assertEqual(len(result["state"]["history"]), 3)

    def test_observation_normalization_and_policies(self):
        observation = ObservationManager().normalize({"success": True, "message": "ok"})
        self.assertEqual(observation.output, "ok")
        self.assertEqual(ConfidenceRouter().route(0.91), "reflect")
        self.assertEqual(ReasoningErrorClassifier().classify("ImportError in app"), "ImportError")
        self.assertEqual(RetryStrategy().next_action("modify_project", "validation failed"), "reflection")
        self.assertEqual(FailureRecovery(2).decide(2, "error"), "stop")


if __name__ == "__main__":
    unittest.main()