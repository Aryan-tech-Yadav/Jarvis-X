from unittest.mock import Mock

from app.tools.base_tool import BaseTool, ToolMetadata
from app.tools.tool_manager import ToolManager


class ExplodingTool(BaseTool):
    metadata = ToolMetadata(
        name="exploding",
        permissions=[],
    )

    def __init__(self):
        super().__init__()
        self.calls = 0

    def run(self, action=None, **kwargs):
        self.calls += 1
        raise TypeError("simulated internal error")


def test_tool_manager_does_not_retry_after_type_error():
    tool = ExplodingTool()
    manager = ToolManager()
    manager.register("exploding", tool)

    result = manager.execute("exploding", "run")

    assert result["success"] is False
    assert "TypeError" in result["error"]
    assert tool.calls == 1


def test_tool_manager_denies_dangerous_permission_without_execution():
    permission_manager = Mock()
    permission_manager.check.return_value.allowed = False
    permission_manager.check.return_value.reason = "Permission denied"

    manager = ToolManager(permission_manager=permission_manager)
    tool = ExplodingTool()
    tool.metadata.permissions = ["filesystem.delete"]
    manager.register("exploding", tool)

    result = manager.execute("exploding", "run")

    assert result["success"] is False
    assert result["error"] == "Permission denied"
    assert tool.calls == 0
