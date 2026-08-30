"""Jarvis-X Tool Ecosystem.

Provides a unified, extensible tool system with:
  - BaseTool: abstract base class
  - ToolMetadata, ToolResult: data contracts
  - ToolRegistry: central tool registry
  - ToolLoader: dynamic tool discovery
  - ToolExecutor: dispatch through registry
  - ToolSelector: capability-based selection
  - PermissionManager: safety and approval
  - ToolChain: multi-step workflows
  - Built-in tools: filesystem, git, docker, browser, internet, memory, database, vscode, automation
"""

from app.tools.tool import BaseTool, ToolMetadata
from app.tools.tool_result import ToolResult
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_executor import ToolExecutor
from app.tools.tool_selector import ToolSelector
from app.tools.tool_ranker import ToolRanker
from app.tools.tool_cache import ToolCache
from app.tools.tool_history import ToolHistory, ToolCall
from app.tools.tool_loader import ToolLoader, LoadedTool
from app.tools.permission_manager import PermissionManager, PermissionRule, PermissionResult
from app.tools.tool_chain import ToolChain, ChainStep, ChainResult
from app.tools.filesystem import FileSystemTool
from app.tools.git import GitTool
from app.tools.docker import DockerTool
from app.tools.browser import BrowserTool
from app.tools.internet import InternetTool
from app.tools.memory import MemoryTool
from app.tools.database import DatabaseTool
from app.tools.vscode import VSCodeTool
from app.tools.automation import AutomationTool

__all__ = [
    "BaseTool",
    "ToolMetadata",
    "ToolResult",
    "ToolRegistry",
    "ToolExecutor",
    "ToolSelector",
    "ToolRanker",
    "ToolCache",
    "ToolHistory",
    "ToolCall",
    "ToolLoader",
    "LoadedTool",
    "PermissionManager",
    "PermissionRule",
    "PermissionResult",
    "ToolChain",
    "ChainStep",
    "ChainResult",
    "FileSystemTool",
    "GitTool",
    "DockerTool",
    "BrowserTool",
    "InternetTool",
    "MemoryTool",
    "DatabaseTool",
    "VSCodeTool",
    "AutomationTool",
]
