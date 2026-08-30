from app.tools.base_tool import BaseTool
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

    def __init__(self, registry=None, executor=None):
        self.registry = registry or ToolRegistry()
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
            if action is None:
                result = tool.execute(context=context, **kwargs)
            else:
                result = tool.execute(action, context=context, **kwargs)
            self.history.record(ToolCall(tool_name, 0.0, bool(result.get("success")) if isinstance(result, dict) else True))
            return result
        except TypeError:
            try:
                return tool.execute(context or kwargs)
            except TypeError:
                return tool.execute(action, context)
        except Exception as exc:  # pragma: no cover - defensive safety net
            return {"success": False, "output": "", "error": str(exc)}

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
            "run_pip": TerminalTool(),
            "run_pytest": TerminalTool(),
            "read_file": FileTool(),
            "write_file": FileTool(),
        }

        for name, tool in default_tools.items():
            if self.registry.get(name) is None:
                self.registry.register(name, tool)


class _ExecutorTool(BaseTool):

    def __init__(self, executor, name):
        self.executor = executor
        self.name = name

    def run(self, action=None, **kwargs):
        base_path = kwargs.get("base_path")
        payload = dict(kwargs)
        payload.pop("base_path", None)
        if self.name == "run_python":
            payload.setdefault("file_name", "main.py")
        elif self.name in {"read_file", "write_file"}:
            payload.setdefault("file_name", action or payload.get("path"))
        return self.executor.execute(self.name, base_path, **payload)
