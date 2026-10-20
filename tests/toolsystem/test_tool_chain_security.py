from unittest.mock import Mock

from app.tools.base_tool import BaseTool, ToolMetadata
from app.tools.permission_manager import PermissionManager
from app.tools.tool_chain import ToolChain
from app.tools.tool_registry import ToolRegistry


class CountingTool(BaseTool):
    metadata = ToolMetadata(
        name="counting",
        actions=["run"],
        permissions=["terminal.sudo"],
    )

    def __init__(self):
        super().__init__()
        self.calls = 0

    def run(self, action=None, **kwargs):
        self.calls += 1
        return {"success": True, "output": "executed"}


def test_chain_inherits_registry_permission_manager():
    pm = PermissionManager()
    registry = ToolRegistry(permission_manager=pm)

    chain = ToolChain(registry=registry)

    assert chain.permission_manager is pm


def test_chain_does_not_execute_tool_when_permission_denied():
    pm = Mock()
    pm.check.return_value.allowed = False
    pm.check.return_value.reason = "Permission denied"

    registry = ToolRegistry(permission_manager=pm)
    tool = CountingTool()
    registry.register(tool)

    chain = ToolChain(registry=registry)
    chain.add("counting", "run")

    result = chain.execute_all()

    assert result.success is False
    assert tool.calls == 0
    pm.check.assert_called_once_with(
        "counting", "run", ["terminal.sudo"]
    )


def test_chain_uses_tool_metadata_permissions():
    pm = Mock()
    pm.check.return_value.allowed = True

    registry = ToolRegistry(permission_manager=pm)
    tool = CountingTool()
    registry.register(tool)

    chain = ToolChain(registry=registry)
    chain.add("counting", "run")

    result = chain.execute_all()

    assert result.success is True
    assert tool.calls == 1
    pm.check.assert_called_once_with(
        "counting", "run", ["terminal.sudo"]
    )


def test_chain_denies_dangerous_permission_without_permission_manager():
    registry = ToolRegistry()
    tool = CountingTool()
    registry.register(tool)

    chain = ToolChain(registry=registry)
    chain.add("counting", "run")

    result = chain.execute_all()

    assert result.success is False
    assert tool.calls == 0
    assert any("Permission" in error for error in result.errors)
