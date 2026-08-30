"""Tool execution validator for post-operation state verification."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from app.core.results import ExecutionResult


class ToolValidator:
    """Verifies that tool execution achieved its expected side-effects on disk and state."""

    @staticmethod
    def validate_filesystem_output(path: str, expected_exists: bool = True) -> bool:
        p = Path(path)
        if expected_exists:
            return p.exists() and p.stat().st_size > 0
        return not p.exists()

    @staticmethod
    def validate_execution_result(result: ExecutionResult) -> bool:
        return result.success and result.status in {"completed", "success"}
