"""Minimal release command entry point: `python -m app.release.cli release`."""

import argparse
import json
import os

from app.release.release_pipeline import ReleasePipeline


def main(argv=None):
    parser = argparse.ArgumentParser(prog="jarvis")
    commands = parser.add_subparsers(dest="command", required=True)
    release = commands.add_parser("release", help="run release gates and create artifacts")
    release.add_argument("--output", default="artifacts/releases")
    release.add_argument("--version", default="0.1.0-alpha")
    release.add_argument("--package", action="store_true")
    workspace = commands.add_parser("workspace", help="manage persistent Jarvis-X workspaces")
    workspace_commands = workspace.add_subparsers(dest="workspace_command", required=True)
    for name, help_text, project_argument in (
        ("create", "create a workspace", False),
        ("list", "list workspace projects", False),
        ("doctor", "report workspace health", False),
        ("project-create", "create a project", False),
        ("open", "open an active project", True),
        ("archive", "archive a project", True),
        ("restore", "restore an archived or deleted project", True),
        ("delete", "move a project to recoverable trash", True),
        ("snapshot", "create a project snapshot", True),
    ):
        command = workspace_commands.add_parser(name, help=help_text)
        command.add_argument("path")
        if project_argument:
            command.add_argument("project_id")
        if name == "project-create":
            command.add_argument("name")
            command.add_argument("--description", default="")
    arguments = parser.parse_args(argv)
    if arguments.command == "release":
        result = ReleasePipeline().run(os.path.abspath(arguments.output), version=arguments.version, package=arguments.package)
        print(json.dumps({"success": result["success"], "artifacts": result["artifacts"]}, indent=2))
        return 0 if result["success"] else 1
    if arguments.command == "workspace":
        from app.workspace.workspace_manager import WorkspaceManager

        manager = WorkspaceManager(arguments.path)
        command = arguments.workspace_command
        if command == "create":
            result = {"workspace": str(manager.create_workspace().root)}
        else:
            manager.load_workspace()
            if command == "list":
                result = {"projects": manager.list_projects()}
            elif command == "doctor":
                result = {"workspace": str(manager.workspace.root), "metrics": manager.metrics(), "healthy": True}
            elif command == "project-create":
                result = manager.create_project(arguments.name, arguments.description).to_dict()
            elif command == "open":
                result = manager.open_project(arguments.project_id).to_dict()
            elif command == "archive":
                result = manager.archive_project(arguments.project_id).to_dict()
            elif command == "restore":
                result = manager.restore_project(arguments.project_id).to_dict()
            elif command == "delete":
                result = manager.delete_project(arguments.project_id).to_dict()
            else:  # snapshot
                result = {"snapshot_id": manager.snapshot_project(arguments.project_id)}
        print(json.dumps(result, indent=2, default=str))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
