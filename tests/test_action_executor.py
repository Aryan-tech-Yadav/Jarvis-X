import unittest

from app.reasoning.action import Action
from app.reasoning.action_executor import ActionExecutor


class RecordingTools:
    def __init__(self):
        self.calls = []

    def execute(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return {"success": True, "output": "done"}


class ActionExecutorTests(unittest.TestCase):
    def test_executor_routes_action_to_tool_manager(self):
        tools = RecordingTools()
        result = ActionExecutor(tools).execute(Action("file", "read", {"path": "README.md"}))

        self.assertTrue(result["success"])
        self.assertEqual(tools.calls[0][0], ("file", "read"))
        self.assertEqual(tools.calls[0][1]["path"], "README.md")


if __name__ == "__main__":
    unittest.main()