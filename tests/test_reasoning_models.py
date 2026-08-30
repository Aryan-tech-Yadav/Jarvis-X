import unittest

from app.reasoning.action import Action
from app.reasoning.json_parser import parse_action, parse_thought
from app.reasoning.observation import Observation
from app.reasoning.reasoning_state import ReasoningState
from app.reasoning.thought import Thought


class ReasoningModelTests(unittest.TestCase):
    def test_models_expose_expected_fields(self):
        thought = Thought(text="inspect", confidence=0.8, reasoning="need context")
        action = Action("file", "read", {"path": "README.md"})
        observation = Observation(True, "ok")

        self.assertEqual(thought.text, "inspect")
        self.assertEqual(action.action, "read")
        self.assertTrue(observation.success)

    def test_parser_builds_thought_and_action(self):
        thought = parse_thought('{"thought":"read","tool":"file","action":"read","arguments":{"path":"x"},"finished":true}')

        self.assertEqual(thought.tool, "file")
        self.assertEqual(parse_action(thought.to_dict()).arguments["path"], "x")

    def test_state_history_is_triplet(self):
        state = ReasoningState("inspect")
        state.add_thought({"thought": "read", "step": 1})
        state.add_action({"action": "read"})
        state.add_observation({"success": True})

        self.assertEqual(set(state.history()[0]), {"thought", "action", "observation"})


if __name__ == "__main__":
    unittest.main()