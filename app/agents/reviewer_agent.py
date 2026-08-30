import ast
import os

from app.agents.base_agent import BaseAgent


class ReviewerAgent(BaseAgent):
    """Read-only architecture and source review for a generated project."""

    agent_id = "reviewer"
    capabilities = ("review", "architecture", "security", "quality")

    def run(self, context):
        project_path = self.context_value(context, "project_path") or self.context_value(context, "base_path")
        if not project_path or not os.path.isdir(project_path):
            return {"success": False, "output": {"approved": False, "issues": ["Project path not found."]}}

        issues = []
        python_files = []
        for root, directories, files in os.walk(project_path):
            directories[:] = [name for name in directories if name not in {".git", ".venv", "venv", "__pycache__"}]
            for filename in files:
                if filename.endswith(".py"):
                    python_files.append(os.path.join(root, filename))

        checks = ["architecture", "imports", "naming", "folder_structure", "dead_code", "duplicate_code", "security"]
        if not python_files:
            issues.append("No Python source files were found.")
        if python_files and not any(os.path.basename(path) in {"main.py", "app.py", "game.py"} for path in python_files):
            issues.append("Architecture: no runnable entry point was found.")
        for filename in python_files:
            self._review_file(filename, project_path, issues)

        output = {
            "approved": not issues,
            "issues": issues,
            "files_reviewed": len(python_files),
            "checks": checks,
        }
        self.update_context(context, "review", output)
        return {"success": not issues, "output": output}

    def _review_file(self, filename, project_path, issues):
        relative = os.path.relpath(filename, project_path).replace(os.sep, "/")
        try:
            with open(filename, "r", encoding="utf-8") as source_file:
                source = source_file.read()
            tree = ast.parse(source, filename=relative)
        except (OSError, UnicodeDecodeError, SyntaxError) as error:
            issues.append(f"{relative}: cannot be reviewed ({error})")
            return

        if "eval(" in source or "exec(" in source:
            issues.append(f"{relative}: unsafe dynamic code execution found.")
        if "TODO" in source or "FIXME" in source:
            issues.append(f"{relative}: unfinished TODO/FIXME marker found.")

        top_level_names = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                top_level_names.append(node.name)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.islower():
                    issues.append(f"{relative}: function name '{node.name}' should use snake_case.")
            elif isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names):
                issues.append(f"{relative}: wildcard import reduces import clarity.")
            elif isinstance(node, ast.If) and isinstance(node.test, ast.Constant) and node.test.value is False:
                issues.append(f"{relative}: unreachable 'if False' block found.")
        duplicates = sorted({name for name in top_level_names if top_level_names.count(name) > 1})
        if duplicates:
            issues.append(f"{relative}: duplicate declarations: {', '.join(duplicates)}.")
