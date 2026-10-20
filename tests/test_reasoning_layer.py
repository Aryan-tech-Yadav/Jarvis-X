import unittest

from app.reasoning import Reasoner


class TestReasoningLayer(unittest.TestCase):
    def test_reasoner_validates_executes_and_reflects(self):
        events = []
        decision = Reasoner(event_bus=type("Bus", (), {
            "publish": lambda self, name, payload: events.append((name, payload))
        })()).reason("build a report", execute=lambda plan: {"success": True, "output": "done"})
        self.assertTrue(decision.validation["valid"])
        self.assertEqual(decision.reflection["outcome"], "success")
        self.assertEqual(events[0][0], "REASONING_COMPLETED")

    def test_empty_goal_is_rejected(self):
        with self.assertRaises(ValueError):
            Reasoner().reason(" ")


if __name__ == "__main__":
    unittest.main()
