"""Git tool.

Actions: clone, status, diff, log, commit, push, pull, branch, checkout
"""

from __future__ import annotations

import os
import subprocess

from app.tools.base_tool import BaseTool, ToolMetadata, ToolResult


class GitTool(BaseTool):
    metadata = ToolMetadata(
        name="git",
        description="Git version control operations",
        version="1.0.0",
        author="Jarvis",
        actions=["clone", "status", "diff", "log", "commit", "push", "pull", "branch", "checkout", "init"],
        permissions=["git.read", "git.write"],
        tags=["git", "version-control", "vcs"],
    )

    def run(self, action: str = "", **kwargs) -> dict:
        if action not in self.metadata.actions:
            return ToolResult.fail(f"Unsupported action: {action}").to_dict()

        cwd = kwargs.get("cwd") or kwargs.get("base_path") or os.getcwd()

        try:
            if action == "init":
                subprocess.run(["git", "init"], cwd=cwd, capture_output=True, check=True)
                return ToolResult.ok(output="Initialized git repo").to_dict()

            if action == "clone":
                repo = kwargs.get("repo") or kwargs.get("url")
                if not repo:
                    return ToolResult.fail("Repository URL is required").to_dict()
                dest = kwargs.get("destination", os.path.basename(repo).replace(".git", ""))
                subprocess.run(["git", "clone", repo, dest], cwd=cwd, capture_output=True, check=True)
                return ToolResult.ok(output=os.path.join(cwd, dest), artifacts=[os.path.join(cwd, dest)]).to_dict()

            if action == "status":
                result = subprocess.run(["git", "status", "--short"], cwd=cwd, capture_output=True, text=True)
                return ToolResult.ok(output=result.stdout.strip()).to_dict()

            if action == "diff":
                result = subprocess.run(["git", "diff"], cwd=cwd, capture_output=True, text=True)
                return ToolResult.ok(output=result.stdout).to_dict()

            if action == "log":
                count = kwargs.get("count", 10)
                result = subprocess.run(["git", "log", f"--oneline", f"-n{count}"], cwd=cwd, capture_output=True, text=True)
                return ToolResult.ok(output=result.stdout.strip()).to_dict()

            if action == "commit":
                message = kwargs.get("message", "Auto commit")
                subprocess.run(["git", "add", "."], cwd=cwd, capture_output=True, check=True)
                subprocess.run(["git", "commit", "-m", message], cwd=cwd, capture_output=True, check=True)
                return ToolResult.ok(output=f"Committed: {message}").to_dict()

            if action == "branch":
                name = kwargs.get("name")
                if name:
                    subprocess.run(["git", "checkout", "-b", name], cwd=cwd, capture_output=True, check=True)
                    return ToolResult.ok(output=f"Created branch: {name}").to_dict()
                result = subprocess.run(["git", "branch", "--show-current"], cwd=cwd, capture_output=True, text=True)
                return ToolResult.ok(output=result.stdout.strip()).to_dict()

            if action == "checkout":
                branch = kwargs.get("branch") or kwargs.get("target")
                if not branch:
                    return ToolResult.fail("Branch name is required").to_dict()
                subprocess.run(["git", "checkout", branch], cwd=cwd, capture_output=True, check=True)
                return ToolResult.ok(output=f"Checked out: {branch}").to_dict()

            if action == "push":
                remote = kwargs.get("remote", "origin")
                branch = kwargs.get("branch", "")
                cmd = ["git", "push", remote]
                if branch:
                    cmd.append(branch)
                subprocess.run(cmd, cwd=cwd, capture_output=True, check=True)
                return ToolResult.ok(output=f"Pushed to {remote}").to_dict()

            if action == "pull":
                remote = kwargs.get("remote", "origin")
                branch = kwargs.get("branch", "")
                cmd = ["git", "pull", remote]
                if branch:
                    cmd.append(branch)
                subprocess.run(cmd, cwd=cwd, capture_output=True, check=True)
                return ToolResult.ok(output=f"Pulled from {remote}").to_dict()

        except subprocess.CalledProcessError as exc:
            return ToolResult.fail(exc.stderr or str(exc)).to_dict()
        except OSError as exc:
            return ToolResult.fail(str(exc)).to_dict()

        return ToolResult.fail(f"Unhandled action: {action}").to_dict()
