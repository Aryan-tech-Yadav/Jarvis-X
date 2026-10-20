from app.tools.base_tool import BaseTool
from app.tools.permission_manager import PermissionManager
from app.tools.command_runner import CommandRunner
from app.tools.file_tool import FileTool
from app.tools.python_tool import PythonTool
from app.tools.search_tool import SearchTool
from app.tools.terminal_tool import TerminalTool
from app.tools.tool_executor import ToolExecutor
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_cache import ToolCache
from app.tools.tool_history import ToolCall, ToolHistory


class ToolManager:

    def __init__(self, registry=None, executor=None, permission_manager=None):
        self.permission_manager = (
            permission_manager
            or getattr(registry, "_permission_manager", None)
            or PermissionManager()
        )
        self.registry = registry or ToolRegistry(
            permission_manager=self.permission_manager
        )
        if getattr(self.registry, "_permission_manager", None) is None:
            self.registry._permission_manager = self.permission_manager

        self.executor = executor or ToolExecutor()
        self.history = ToolHistory()
        self.cache = ToolCache()
        self._register_defaults()

    def execute(self, tool_name, action=None, *args, **kwargs):
        context = {}
        for item in args:
            if isinstance(item, dict):
                context.update(item)
            elif item is not None and action is None:
                action = item

        if "context" in kwargs and isinstance(kwargs["context"], dict):
            context.update(kwargs.pop("context"))

        if isinstance(action, dict):
            context.update(action)
            action = None

        base_path = kwargs.pop("base_path", context.get("base_path"))
        if base_path is not None:
            context.setdefault("base_path", base_path)

        if action is None and "action" in kwargs:
            action = kwargs.pop("action")

        if action is None and "request" in kwargs:
            action = kwargs.pop("request")

        if action is not None and not isinstance(action, str):
            context.setdefault("request", action)
            action = None

        tool = self.registry.get(tool_name)
        if tool is None:
            return {"success": False, "output": "", "error": f"Unknown tool: {tool_name}"}

        try:
            permission_result = self.permission_manager.check(
                tool_name,
                action or "",
                tool.metadata.permissions or [],
            )
            if not permission_result.allowed:
                denied = {
                    "success": False,
                    "output": "",
                    "error": permission_result.reason or "Permission denied",
                }
                self.history.record(ToolCall(tool_name, 0.0, False))
                return denied

            if action is None:
                result = tool.execute(context=context, **kwargs)
            else:
                result = tool.execute(action, context=context, **kwargs)
            self.history.record(ToolCall(tool_name, 0.0, bool(result.get("success")) if isinstance(result, dict) else True))
            return result
        except Exception as exc:  # Never retry tool execution after an exception.
            self.history.record(ToolCall(tool_name, 0.0, False))
            return {
                "success": False,
                "output": "",
                "error": f"{type(exc).__name__}: {exc}",
            }

    def register(self, name, tool):
        self.registry.register(name, tool)

    def names(self):
        return self.registry.names()

    def _register_defaults(self):
        default_tools = {
            "file": FileTool(),
            "terminal": TerminalTool(),
            "python": PythonTool(),
            "search": SearchTool(),
            "run_python": PythonTool(),
            "run_pip": _CommandRunnerTool(CommandRunner(), "run_pip"),
            "run_pytest": _CommandRunnerTool(CommandRunner(), "run_pytest"),
            "read_file": FileTool(),
            "write_file": FileTool(),
        }

        for name, tool in default_tools.items():
            if self.registry.get(name) is None:
                self.registry.register(name, tool)


class _ExecutorTool(BaseTool):

    def __init__(self, executor, name):
        super().__init__()
        self.executor = executor
        self._tool_name = name
        self.metadata.name = name

    def run(self, action=None, **kwargs):
        base_path = kwargs.get("base_path")
        payload = dict(kwargs)
        payload.pop("base_path", None)
        if self._tool_name == "run_python":
            payload.setdefault("file_name", "main.py")
        elif self._tool_name in {"read_file", "write_file"}:
            payload.setdefault("file_name", action or payload.get("path"))
        return self.executor.execute(self.name, base_path, **payload)


class _CommandRunnerTool(BaseTool):
    """Expose bounded project commands through the standard tool interface."""

    def __init__(self, runner, name):
        super().__init__()
        self.runner = runner
        self._tool_name = name
        self.metadata.name = name

    def run(self, action=None, **kwargs):
        context = kwargs.get("context") or {}
        base_path = (
            kwargs.get("base_path")
            or kwargs.get("cwd")
            or context.get("base_path")
            or context.get("cwd")
        )
        if not base_path:
            return {
                "success": False,
                "output": "",
                "error": "base_path is required",
            }

        if self._tool_name == "run_pip":
            result = self.runner.run_pip(base_path)
        elif self._tool_name == "run_pytest":
            result = self.runner.run_pytest(base_path)
        else:
            return {
                "success": False,
                "output": "",
                "error": "Unsupported command alias",
            }

        return result.to_dict()
