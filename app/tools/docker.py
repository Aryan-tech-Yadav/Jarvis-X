"""Docker tool.

Actions: build, run, ps, logs, stop, rm, images, pull
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import tempfile


_MAX_CAPTURE_BYTES = 20000


def _run_bounded(*args, capture_output=False, text=False, check=False,
                 timeout=None, **kwargs):
    """Run a subprocess with bounded in-memory output capture."""
    if not capture_output:
        return subprocess.run(
            *args, text=text, check=check, timeout=timeout, **kwargs
        )

    with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        completed = subprocess.run(
            *args,
            stdout=stdout_file,
            stderr=stderr_file,
            timeout=timeout,
            check=False,
            **kwargs,
        )

        def read_capped(file):
            file.seek(0)
            data = file.read(_MAX_CAPTURE_BYTES + 1)
            truncated = len(data) > _MAX_CAPTURE_BYTES
            result = data[:_MAX_CAPTURE_BYTES].decode("utf-8", errors="replace")
            if truncated:
                result += "\\n...[output truncated]"
            return result

        stdout = read_capped(stdout_file)
        stderr = read_capped(stderr_file)

    result = subprocess.CompletedProcess(
        completed.args, completed.returncode, stdout, stderr
    )

    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, result.args, output=result.stdout, stderr=result.stderr
        )

    return result


from app.tools.base_tool import BaseTool, ToolMetadata, ToolResult


class DockerTool(BaseTool):
    metadata = ToolMetadata(
        name="docker",
        description="Docker container and image operations",
        version="1.0.0",
        author="Jarvis",
        actions=["build", "run", "ps", "logs", "stop", "rm", "images", "pull", "exec"],
        permissions=["docker.read", "docker.write", "docker.privileged"],
        tags=["docker", "containers", "devops"],
    )

    DEFAULT_TIMEOUT = 30
    MAX_OUTPUT_CHARS = 20000

    def _truncate(self, value):
        value = value or ""
        if len(value) > self.MAX_OUTPUT_CHARS:
            return value[:self.MAX_OUTPUT_CHARS] + "\\n...[output truncated]"
        return value

    def run(self, action: str = "", **kwargs) -> dict:
        if action not in self.metadata.actions:
            return ToolResult.fail(f"Unsupported action: {action}").to_dict()

        cwd = kwargs.get("cwd") or kwargs.get("base_path") or os.getcwd()
        if not isinstance(cwd, (str, os.PathLike)):
            return ToolResult.fail("Invalid working directory").to_dict()

        cwd = os.path.abspath(os.fspath(cwd))
        if not os.path.isdir(cwd):
            return ToolResult.fail("Working directory must exist").to_dict()

        try:
            timeout = float(kwargs.get("timeout", self.DEFAULT_TIMEOUT))
            if not 1 <= timeout <= 300:
                raise ValueError
        except (TypeError, ValueError, OverflowError):
            return ToolResult.fail(
                "Timeout must be a number between 1 and 300 seconds"
            ).to_dict()

        try:
            if action == "build":
                tag = kwargs.get("tag", "latest")
                dockerfile = kwargs.get("dockerfile", "Dockerfile")
                cmd = ["docker", "build", "-t", tag, "-f", dockerfile, "."]
                result = _run_bounded(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
                return self._result(result)

            if action == "run":
                image = kwargs.get("image")
                if not isinstance(image, str) or not image.strip() or image.startswith("-"):
                    return ToolResult.fail("A valid image name is required").to_dict()
                ports = kwargs.get("ports", [])
                env = kwargs.get("env", {})

                if not isinstance(ports, (list, tuple)):
                    return ToolResult.fail("ports must be a list").to_dict()
                if not isinstance(env, dict):
                    return ToolResult.fail("env must be a dictionary").to_dict()

                for port in ports:
                    if not isinstance(port, (str, int)) or isinstance(port, bool):
                        return ToolResult.fail("Invalid port mapping").to_dict()
                    port = str(port)
                    if not port or port.startswith("-") or any(
                        char not in "0123456789:./" for char in port
                    ):
                        return ToolResult.fail("Invalid port mapping").to_dict()

                for key, value in env.items():
                    if (
                        not isinstance(key, str)
                        or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key)
                        or not isinstance(value, (str, int, float))
                        or isinstance(value, bool)
                    ):
                        return ToolResult.fail("Invalid environment variable").to_dict()

                cmd = ["docker", "run", "--rm"]
                for port in ports:
                    cmd.extend(["-p", str(port)])
                for key, value in env.items():
                    cmd.extend(["-e", f"{key}={value}"])
                cmd.append(image)
                result = _run_bounded(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
                return self._result(result)

            if action == "ps":
                result = _run_bounded(["docker", "ps", "-a", "--format", "{{.Names}} {{.Status}}"],
                                        cwd=cwd, capture_output=True, text=True, timeout=timeout)
                return ToolResult.ok(output=self._truncate(result.stdout.strip())).to_dict()

            if action == "logs":
                container = kwargs.get("container")
                if not isinstance(container, str) or not container.strip() or container.startswith("-"):
                    return ToolResult.fail("A valid container name is required").to_dict()
                result = _run_bounded(["docker", "logs", container], cwd=cwd, capture_output=True, text=True, timeout=timeout)
                return ToolResult.ok(output=self._truncate((result.stdout or '') + (result.stderr or ''))).to_dict()

            if action == "stop":
                container = kwargs.get("container")
                if not isinstance(container, str) or not container.strip() or container.startswith("-"):
                    return ToolResult.fail("A valid container name is required").to_dict()
                _run_bounded(["docker", "stop", container], cwd=cwd, capture_output=True, check=True, timeout=timeout)
                return ToolResult.ok(output=f"Stopped: {container}").to_dict()

            if action == "rm":
                container = kwargs.get("container")
                if not isinstance(container, str) or not container.strip() or container.startswith("-"):
                    return ToolResult.fail("A valid container name is required").to_dict()
                _run_bounded(["docker", "rm", container], cwd=cwd, capture_output=True, check=True, timeout=timeout)
                return ToolResult.ok(output=f"Removed: {container}").to_dict()

            if action == "images":
                result = _run_bounded(["docker", "images", "--format", "{{.Repository}}:{{.Tag}} {{.ID}} {{.Size}}"],
                                        cwd=cwd, capture_output=True, text=True, timeout=timeout)
                return ToolResult.ok(output=self._truncate(result.stdout.strip())).to_dict()

            if action == "pull":
                image = kwargs.get("image")
                if not isinstance(image, str) or not image.strip() or image.startswith("-"):
                    return ToolResult.fail("A valid image name is required").to_dict()
                result = _run_bounded(["docker", "pull", image], cwd=cwd, capture_output=True, text=True, timeout=timeout)
                return self._result(result)

            if action == "exec":
                container = kwargs.get("container")
                cmd = kwargs.get("command")
                if not isinstance(container, str) or not container.strip() or container.startswith("-"):
                    return ToolResult.fail("A valid container name is required").to_dict()
                if isinstance(cmd, str):
                    try:
                        cmd = shlex.split(cmd)
                    except ValueError:
                        return ToolResult.fail("Invalid command quoting").to_dict()
                elif isinstance(cmd, (list, tuple)):
                    cmd = list(cmd)
                else:
                    return ToolResult.fail("Command must be a string or argument list").to_dict()

                if not cmd or any(not isinstance(arg, str) or not arg for arg in cmd):
                    return ToolResult.fail("Command arguments must be non-empty strings").to_dict()

                full_cmd = ["docker", "exec", container] + cmd
                result = _run_bounded(full_cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
                return self._result(result)

        except subprocess.TimeoutExpired:
            return ToolResult.fail(f"Docker command timed out after {timeout:g} seconds").to_dict()
        except subprocess.CalledProcessError as exc:
            return ToolResult.fail(exc.stderr or str(exc)).to_dict()
        except (OSError, ValueError) as exc:
            return ToolResult.fail(str(exc)).to_dict()

        return ToolResult.fail(f"Unhandled action: {action}").to_dict()

    def _result(self, result) -> dict:
        output = (result.stdout or "").strip()
        error = (result.stderr or "").strip()
        if len(output) > self.MAX_OUTPUT_CHARS:
            output = output[:self.MAX_OUTPUT_CHARS] + "\n...[output truncated]"
        if len(error) > self.MAX_OUTPUT_CHARS:
            error = error[:self.MAX_OUTPUT_CHARS] + "\n...[output truncated]"
        if result.returncode == 0:
            return ToolResult.ok(output=output).to_dict()
        return ToolResult.fail(error or "Docker command failed", output=output).to_dict()
