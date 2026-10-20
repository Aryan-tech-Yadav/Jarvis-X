"""Git tool.

Actions: clone, status, diff, log, commit, push, pull, branch, checkout
"""

from __future__ import annotations

import os
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

    DEFAULT_TIMEOUT = 30
    MAX_OUTPUT_CHARS = 20000

    def _truncate(self, value):
        value = value or ""
        if len(value) > self.MAX_OUTPUT_CHARS:
            return value[:self.MAX_OUTPUT_CHARS] + "\n...[output truncated]"
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
            if action == "init":
                _run_bounded(["git", "init"], cwd=cwd, capture_output=True, check=True, timeout=timeout)
                return ToolResult.ok(output="Initialized git repo").to_dict()

            if action == "clone":
                repo = kwargs.get("repo") or kwargs.get("url")
                if not isinstance(repo, str) or not repo.strip() or repo.startswith("-"):
                    return ToolResult.fail("A valid repository URL is required").to_dict()

                dest = kwargs.get("destination")
                if dest is None:
                    dest = os.path.basename(repo.rstrip("/")).removesuffix(".git")

                if not isinstance(dest, str) or not dest.strip() or dest.startswith("-"):
                    return ToolResult.fail("A valid clone destination is required").to_dict()

                base_dir = os.path.realpath(cwd)
                dest_path = os.path.abspath(os.path.join(base_dir, dest))
                if os.path.commonpath([base_dir, dest_path]) != base_dir or dest_path == base_dir:
                    return ToolResult.fail("Clone destination must be a child of the working directory").to_dict()

                if os.path.lexists(dest_path):
                    return ToolResult.fail("Clone destination already exists").to_dict()

                _run_bounded(
                    ["git", "clone", "--", repo, dest_path],
                    cwd=base_dir, capture_output=True, check=True, timeout=timeout,
                )
                return ToolResult.ok(output=dest_path, artifacts=[dest_path]).to_dict()

            if action == "status":
                result = _run_bounded(["git", "status", "--short"], cwd=cwd, capture_output=True, text=True, timeout=timeout)
                return ToolResult.ok(output=self._truncate(result.stdout.strip())).to_dict()

            if action == "diff":
                result = _run_bounded(["git", "diff"], cwd=cwd, capture_output=True, text=True, timeout=timeout)
                return ToolResult.ok(output=self._truncate(result.stdout)).to_dict()

            if action == "log":
                count = kwargs.get("count", 10)
                if isinstance(count, bool) or not (
                    isinstance(count, int)
                    or (isinstance(count, str) and count.isdigit())
                ):
                    return ToolResult.fail("Log count must be an integer from 1 to 100").to_dict()
                count = int(count)
                if not 1 <= count <= 100:
                    return ToolResult.fail("Log count must be an integer from 1 to 100").to_dict()
                result = _run_bounded(
                    ["git", "log", "--oneline", f"-n{count}"],
                    cwd=cwd, capture_output=True, text=True, timeout=timeout,
                )
                return ToolResult.ok(output=self._truncate(result.stdout.strip())).to_dict()

            if action == "commit":
                message = kwargs.get("message", "Auto commit")
                if not isinstance(message, str) or not message.strip():
                    return ToolResult.fail("Commit message must be a non-empty string").to_dict()
                _run_bounded(
                    ["git", "commit", "-m", message],
                    cwd=cwd, capture_output=True, text=True,
                    check=True, timeout=timeout,
                )
                return ToolResult.ok(output=f"Committed: {message}").to_dict()

            if action == "branch":
                name = kwargs.get("name")
                if name:
                    if not isinstance(name, str) or not name.strip() or name.startswith("-"):
                        return ToolResult.fail("Invalid branch name").to_dict()
                    _run_bounded(
                        ["git", "check-ref-format", "--branch", name],
                        cwd=cwd, capture_output=True, text=True,
                        check=True, timeout=timeout,
                    )
                    _run_bounded(
                        ["git", "checkout", "-b", name],
                        cwd=cwd, capture_output=True, text=True,
                        check=True, timeout=timeout,
                    )
                    return ToolResult.ok(output=f"Created branch: {name}").to_dict()
                result = _run_bounded(["git", "branch", "--show-current"], cwd=cwd, capture_output=True, text=True, timeout=timeout)
                return ToolResult.ok(output=self._truncate(result.stdout.strip())).to_dict()

            if action == "checkout":
                branch = kwargs.get("branch") or kwargs.get("target")
                if not isinstance(branch, str) or not branch.strip() or branch.startswith("-"):
                    return ToolResult.fail("A valid branch or revision is required").to_dict()
                _run_bounded(
                    ["git", "checkout", branch],
                    cwd=cwd, capture_output=True, text=True,
                    check=True, timeout=timeout,
                )
                return ToolResult.ok(output=f"Checked out: {branch}").to_dict()

            if action == "push":
                remote = kwargs.get("remote", "origin")
                branch = kwargs.get("branch", "")
                if not isinstance(remote, str) or not remote.strip() or remote.startswith("-"):
                    return ToolResult.fail("Invalid remote name").to_dict()
                if branch and (
                    not isinstance(branch, str) or not branch.strip() or branch.startswith("-")
                ):
                    return ToolResult.fail("Invalid branch name").to_dict()
                cmd = ["git", "push", remote]
                if branch:
                    cmd.append(branch)
                _run_bounded(cmd, cwd=cwd, capture_output=True, check=True, timeout=timeout)
                return ToolResult.ok(output=f"Pushed to {remote}").to_dict()

            if action == "pull":
                remote = kwargs.get("remote", "origin")
                branch = kwargs.get("branch", "")
                if not isinstance(remote, str) or not remote.strip() or remote.startswith("-"):
                    return ToolResult.fail("Invalid remote name").to_dict()
                if branch and (
                    not isinstance(branch, str) or not branch.strip() or branch.startswith("-")
                ):
                    return ToolResult.fail("Invalid branch name").to_dict()
                cmd = ["git", "pull", remote]
                if branch:
                    cmd.append(branch)
                _run_bounded(cmd, cwd=cwd, capture_output=True, check=True, timeout=timeout)
                return ToolResult.ok(output=f"Pulled from {remote}").to_dict()

        except subprocess.TimeoutExpired:
            return ToolResult.fail(f"Git command timed out after {timeout:g} seconds").to_dict()
        except subprocess.CalledProcessError as exc:
            return ToolResult.fail(exc.stderr or str(exc)).to_dict()
        except (OSError, ValueError) as exc:
            return ToolResult.fail(str(exc)).to_dict()

        return ToolResult.fail(f"Unhandled action: {action}").to_dict()
