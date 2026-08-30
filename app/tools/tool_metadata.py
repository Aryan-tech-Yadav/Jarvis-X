"""Tool metadata schema.

Kept for backward compatibility.
Prefer importing ToolMetadata from app.tools.base_tool.
"""

from app.tools.base_tool import ToolMetadata as ToolMetadata

__all__ = ["ToolMetadata"]
