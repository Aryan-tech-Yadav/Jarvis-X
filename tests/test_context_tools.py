import unittest

from app.context.context_manager import ContextManager
from app.context.context_summary import ContextSummary
from app.context.context_window import ContextWindow
from app.tools.tool_metadata import ToolMetadata
from app.tools.tool_selector import ToolSelector


class MetadataRegistry:
    def __init__(self, tools):
        self.tools = tools

    def list(self):
        return self.tools


class ContextToolsTests(unittest.TestCase):
    def test_context_manager_builds_windowed_context(self):
        manager = ContextManager()
        context = manager.build("goal", "project", "step", list(range(12)), list(range(7)))

        self.assertEqual(context["goal"], "goal")
        self.assertEqual(len(context["conversation"]), 10)
        self.assertEqual(len(context["reasoning"]), 5)

    def test_context_summary_compresses_large_history(self):
        result = ContextSummary(threshold=2).summarize([1, 2, 3])

        self.assertIn("Summarized", result["summary"])
        self.assertEqual(result["entries"], [1, 2, 3][-10:])

    def test_tool_selector_uses_capability_action_and_priority(self):
        tools = [
            ToolMetadata("terminal", "execute commands", ["run"], priority=1),
            ToolMetadata("test-runner", "run tests", ["run"], priority=5),
        ]

        selected = ToolSelector(MetadataRegistry(tools)).select("run tests", "run")

        self.assertEqual(selected.name, "test-runner")


if __name__ == "__main__":
    unittest.main()