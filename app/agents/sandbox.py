"""Isolated execution environment and path boundary for dynamically spawned agents."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from app.tools.process_utils import run_bounded


class AgentSandbox:
    """Provides path boundary protection and isolated execution for agent tasks."""

    DEFAULT_TIMEOUT = 30.0
    MAX_TIMEOUT = 300.0
    MAX_OUTPUT_CHARS = 20000

    SENSITIVE_ENV_KEYS = {
        "API_KEY",
        "DEEPGRAM_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "MY_API_KEY",
        "SECRET_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "GITHUB_TOKEN",
        "DATABASE_URL",
    }

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, relative_path: str) -> Path:
        if not relative_path or not str(relative_path).strip():
            raise ValueError("Sandbox path cannot be empty")
        candidate = (self.root / relative_path).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise PermissionError("Agent path escapes sandbox")
        return candidate

    def contains(self, target: str) -> bool:
        try:
            self.path(target)
            return True
        except (PermissionError, ValueError):
            return False

    def build_sanitized_env(self, custom_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Strip host credentials, tokens, and sensitive secrets from child process environment."""
        sanitized: Dict[str, str] = {}
        safe_keys = {
            "PATH",
            "PYTHONPATH",
            "SYSTEMROOT",
            "TEMP",
            "TMP",
            "HOME",
            "USER",
            "LANG",
            "LC_ALL",
        }

        for key, value in os.environ.items():
            upper = key.upper()
            if key in safe_keys:
                sanitized[key] = value
            elif any(s in upper for s in ("TOKEN", "SECRET", "KEY", "PASS", "AUTH")):
                continue
            elif key in self.SENSITIVE_ENV_KEYS:
                continue
            else:
                sanitized[key] = value

        if custom_env:
            for k, v in custom_env.items():
                if k not in self.SENSITIVE_ENV_KEYS:
                    sanitized[k] = str(v)

        return sanitized

    def execute_code(
        self,
        code: str,
        filename: str = "_runner_temp.py",
        timeout: float = DEFAULT_TIMEOUT,
        env_vars: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Atomically write and execute Python code inside the sandbox under strict resource limits."""
        if not isinstance(code, str) or not code.strip():
            return {
                "success": False,
                "stdout": "",
                "stderr": "Code cannot be empty",
                "returncode": -1,
                "timed_out": False,
            }

        target_file = self.path(filename)
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(code, encoding="utf-8")

        timeout_sec = max(1.0, min(float(timeout), self.MAX_TIMEOUT))
        env = self.build_sanitized_env(env_vars)

        try:
            completed = run_bounded(
                [sys.executable, str(target_file)],
                max_output_chars=self.MAX_OUTPUT_CHARS,
                cwd=str(self.root),
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                check=False,
            )
            return {
                "success": completed.returncode == 0,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
                "returncode": completed.returncode,
                "timed_out": False,
            }
        except subprocess.TimeoutExpired as exc:
            return {
                "success": False,
                "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
                "stderr": f"Execution timed out after {timeout_sec:g}s",
                "returncode": -1,
                "timed_out": True,
            }
        except Exception as exc:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(exc),
                "returncode": -1,
                "timed_out": False,
            }
        finally:
            # Clean up runner file if it was temporary
            if filename.startswith("_runner_temp") and target_file.is_file():
                try:
                    target_file.unlink()
                except OSError:
                    pass
