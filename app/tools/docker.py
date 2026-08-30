"""Docker tool.

Actions: build, run, ps, logs, stop, rm, images, pull
"""

from __future__ import annotations

import os
import subprocess

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

    def run(self, action: str = "", **kwargs) -> dict:
        if action not in self.metadata.actions:
            return ToolResult.fail(f"Unsupported action: {action}").to_dict()

        cwd = kwargs.get("cwd") or kwargs.get("base_path") or os.getcwd()

        try:
            if action == "build":
                tag = kwargs.get("tag", "latest")
                dockerfile = kwargs.get("dockerfile", "Dockerfile")
                cmd = ["docker", "build", "-t", tag, "-f", dockerfile, "."]
                result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
                return self._result(result)

            if action == "run":
                image = kwargs.get("image")
                if not image:
                    return ToolResult.fail("Image name is required").to_dict()
                ports = kwargs.get("ports", [])
                env = kwargs.get("env", {})
                cmd = ["docker", "run", "--rm"]
                for port in ports:
                    cmd.extend(["-p", str(port)])
                for key, value in env.items():
                    cmd.extend(["-e", f"{key}={value}"])
                cmd.append(image)
                result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
                return self._result(result)

            if action == "ps":
                result = subprocess.run(["docker", "ps", "-a", "--format", "{{.Names}} {{.Status}}"],
                                        cwd=cwd, capture_output=True, text=True)
                return ToolResult.ok(output=result.stdout.strip()).to_dict()

            if action == "logs":
                container = kwargs.get("container")
                if not container:
                    return ToolResult.fail("Container name is required").to_dict()
                result = subprocess.run(["docker", "logs", container], cwd=cwd, capture_output=True, text=True)
                return ToolResult.ok(output=result.stdout + result.stderr).to_dict()

            if action == "stop":
                container = kwargs.get("container")
                if not container:
                    return ToolResult.fail("Container name is required").to_dict()
                subprocess.run(["docker", "stop", container], cwd=cwd, capture_output=True, check=True)
                return ToolResult.ok(output=f"Stopped: {container}").to_dict()

            if action == "rm":
                container = kwargs.get("container")
                if not container:
                    return ToolResult.fail("Container name is required").to_dict()
                subprocess.run(["docker", "rm", container], cwd=cwd, capture_output=True, check=True)
                return ToolResult.ok(output=f"Removed: {container}").to_dict()

            if action == "images":
                result = subprocess.run(["docker", "images", "--format", "{{.Repository}}:{{.Tag}} {{.ID}} {{.Size}}"],
                                        cwd=cwd, capture_output=True, text=True)
                return ToolResult.ok(output=result.stdout.strip()).to_dict()

            if action == "pull":
                image = kwargs.get("image")
                if not image:
                    return ToolResult.fail("Image name is required").to_dict()
                result = subprocess.run(["docker", "pull", image], cwd=cwd, capture_output=True, text=True)
                return self._result(result)

            if action == "exec":
                container = kwargs.get("container")
                cmd = kwargs.get("command")
                if not container or not cmd:
                    return ToolResult.fail("Container and command are required").to_dict()
                full_cmd = ["docker", "exec", container] + (cmd.split() if isinstance(cmd, str) else cmd)
                result = subprocess.run(full_cmd, cwd=cwd, capture_output=True, text=True)
                return self._result(result)

        except subprocess.CalledProcessError as exc:
            return ToolResult.fail(exc.stderr or str(exc)).to_dict()
        except OSError as exc:
            return ToolResult.fail(str(exc)).to_dict()

        return ToolResult.fail(f"Unhandled action: {action}").to_dict()

    def _result(self, result) -> dict:
        if result.returncode == 0:
            return ToolResult.ok(output=(result.stdout or "").strip()).to_dict()
        return ToolResult.fail((result.stderr or "").strip()).to_dict()
