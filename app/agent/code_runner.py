"""Workspace-restricted Python script execution."""

from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

from app.tools.process_utils import run_bounded


class CodeRunner:
    """Run Python scripts contained inside a configured workspace."""

    DEFAULT_TIMEOUT = 30
    MAX_TIMEOUT = 300
    MAX_OUTPUT_CHARS = 20000

    def __init__(self, timeout: float = DEFAULT_TIMEOUT, workspace=None):
        self.workspace = Path(workspace or Path.cwd()).expanduser().resolve()

        try:
            self.timeout = float(timeout)
        except (TypeError, ValueError) as exc:
            raise ValueError("Timeout must be a number between 1 and 300 seconds.") from exc

        if not math.isfinite(self.timeout) or not 1 <= self.timeout <= self.MAX_TIMEOUT:
            raise ValueError("Timeout must be between 1 and 300 seconds.")

    def run(self, script_path):
        """Execute an existing Python file inside the workspace."""
        try:
            if not isinstance(script_path, (str, Path)) or not str(script_path).strip():
                return False, "A valid Python script path is required."

            requested = Path(script_path).expanduser()
            if not requested.is_absolute():
                requested = self.workspace / requested

            script = requested.resolve(strict=True)

            # Reject path traversal and symlinks escaping the workspace.
            if not script.is_relative_to(self.workspace):
                return False, "Script path is outside the configured workspace."

            if not script.is_file() or script.suffix.lower() != ".py":
                return False, "Target must be an existing Python (.py) file."

            completed = run_bounded(
                [sys.executable, str(script)],
                max_output_chars=self.MAX_OUTPUT_CHARS,
                cwd=str(self.workspace),
                shell=False,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )

            output = (completed.stdout or "").strip()
            error = (completed.stderr or "").strip()

            if completed.returncode == 0:
                return True, output

            return False, error or output or (
                f"Script exited with status {completed.returncode}."
            )

        except subprocess.TimeoutExpired:
            return False, f"Script execution timed out after {self.timeout:g} seconds."
        except (OSError, RuntimeError, ValueError, TypeError) as exc:
            return False, f"Script execution rejected or failed: {exc}"
