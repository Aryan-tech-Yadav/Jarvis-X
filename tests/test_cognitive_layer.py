import unittest

from app.cognition import CognitiveOperatingSystem, Goal, GoalStack


class TestCognitiveLayer(unittest.TestCase):
    def test_cos_understands_without_executing(self):
        result = CognitiveOperatingSystem().understand("Build a CRM")
        self.assertEqual(result["decision"]["action"], "plan")
        self.assertEqual(result["goal"]["status"], "pending")

    def test_high_risk_goal_requests_approval(self):
        result = CognitiveOperatingSystem().understand("Deploy to production")
        self.assertEqual(result["decision"]["action"], "ask_user")

    def test_goal_dependencies_control_activation(self):
        stack = GoalStack()
        first = stack.add(Goal("requirements"))
        second = stack.add(Goal("architecture", dependencies=[first.goal_id]))
        self.assertEqual(stack.activate_next().goal_id, first.goal_id)
        self.assertIsNone(stack.activate_next())
        stack.complete(first.goal_id)
        self.assertEqual(stack.activate_next().goal_id, second.goal_id)


if __name__ == "__main__":
    unittest.main()
