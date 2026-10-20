"""File tool.

Legacy wrapper around FileSystemTool.
Kept for backward compatibility.
"""

from __future__ import annotations

from pathlib import Path

from app.tools.base_tool import BaseTool, ToolMetadata, ToolResult


class FileTool(BaseTool):
    metadata = ToolMetadata(
        name="file",
        description="Legacy file operations: read, write, list",
        version="1.0.0",
        author="Jarvis",
        actions=["read", "write", "list", "delete", "exists"],
        permissions=["filesystem.read", "filesystem.write"],
        tags=["filesystem", "file", "legacy"],
    )

    def run(self, action: str = "", **kwargs) -> dict:
        if action not in self.metadata.actions:
            return ToolResult.fail(
                f"Unsupported action: {action}"
            ).to_dict()

        raw_path = kwargs.get("path") or kwargs.get("file_path")
        if not raw_path and action != "list":
            return ToolResult.fail("File path is required").to_dict()

        try:
            raw_workspace = (
                kwargs.get("workspace")
                or kwargs.get("base_path")
                or kwargs.get("cwd")
                or "."
            )
            workspace = Path(raw_workspace).expanduser().resolve(strict=True)

            if not workspace.is_dir():
                return ToolResult.fail(
                    "Workspace must be an existing directory"
                ).to_dict()

            target = Path(raw_path or ".").expanduser()
            if not target.is_absolute():
                target = workspace / target

            # Resolve symlinks in existing paths and parent directories
            # to prevent traversal outside the workspace.
            if action == "write":
                # Canonicalize the complete destination, including ".."
                # segments and existing symlinks, before creating directories.
                resolved = target.resolve(strict=False)
            elif action == "exists":
                resolved = target.resolve(strict=False)
            else:
                resolved = target.resolve(strict=True)

            if not resolved.is_relative_to(workspace):
                return ToolResult.fail(
                    "File operation must remain inside the workspace"
                ).to_dict()

            if action == "read":
                if not resolved.is_file():
                    return ToolResult.fail("Path is not a file").to_dict()
                content = resolved.read_text(encoding="utf-8")
                return ToolResult.ok(output=content).to_dict()

            if action == "write":
                content = kwargs.get("content", "")
                if not isinstance(content, str):
                    return ToolResult.fail(
                        "File content must be a string"
                    ).to_dict()

                # Preserve legacy behavior while keeping directory creation
                # inside the validated workspace boundary.
                resolved.parent.mkdir(parents=True, exist_ok=True)

                # Re-resolve after directory creation to guard against
                # symlinked parent paths escaping the workspace.
                resolved = resolved.parent.resolve(strict=True) / resolved.name
                if not resolved.is_relative_to(workspace):
                    return ToolResult.fail(
                        "File operation must remain inside the workspace"
                    ).to_dict()

                if resolved.exists() and not resolved.is_file():
                    return ToolResult.fail(
                        "Target exists and is not a regular file"
                    ).to_dict()
                resolved.write_text(content, encoding="utf-8")
                return ToolResult.ok(
                    output=str(resolved),
                    artifacts=[str(resolved)],
                ).to_dict()

            if action == "list":
                if not resolved.is_dir():
                    return ToolResult.fail(
                        "Path is not a directory"
                    ).to_dict()
                return ToolResult.ok(
                    output=sorted(p.name for p in resolved.iterdir())
                ).to_dict()

            if action == "exists":
                return ToolResult.ok(output=resolved.exists()).to_dict()

            if action == "delete":
                if not resolved.is_file():
                    return ToolResult.fail(
                        "Delete is restricted to regular files"
                    ).to_dict()
                resolved.unlink()
                return ToolResult.ok(output=str(resolved)).to_dict()

        except (OSError, UnicodeDecodeError, ValueError, TypeError) as exc:
            return ToolResult.fail(str(exc)).to_dict()

        return ToolResult.fail(f"Unhandled action: {action}").to_dict()
