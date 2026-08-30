"""Tool result schema.

Kept for backward compatibility.
Prefer importing ToolResult from app.tools.base_tool.
"""

from app.tools.base_tool import ToolResult as ToolResult
from app.tools.base_tool import ToolResult as UnifiedToolResult

__all__ = ["ToolResult", "UnifiedToolResult"]
