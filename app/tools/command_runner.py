import os
import subprocess
import sys

from config import TIMEOUT
from app.tools.tool_result import ToolResult


class CommandRunner:

    def __init__(self, timeout=TIMEOUT):
        self.timeout = timeout

    def run_python(self, base_path, file_name="main.py"):
        return self.run([sys.executable, file_name], base_path)

    def run_pip(self, base_path):
        return self.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], base_path)

    def run_pytest(self, base_path):
        return self.run([sys.executable, "-m", "pytest"], base_path)

    def run(self, command, base_path):
        if not base_path or not os.path.isdir(base_path):
            return ToolResult(False, error="Invalid project path")

        try:
            result = subprocess.run(
                command,
                cwd=base_path,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(False, error=f"Command timed out after {self.timeout} seconds")
        except OSError as error:
            return ToolResult(False, error=str(error))

        output = result.stdout.strip()
        error = result.stderr.strip()
        return ToolResult(
            success=result.returncode == 0,
            output=output,
            error=error,
            returncode=result.returncode,
        )
