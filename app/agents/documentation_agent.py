import os
from datetime import date

from app.agents.base_agent import BaseAgent


class DocumentationAgent(BaseAgent):
    """Updates project documentation after a successful orchestration run."""

    agent_id = "documentation"
    capabilities = ("documentation", "docs", "readme", "changelog")

    def run(self, context):
        project_path = self.context_value(context, "project_path") or self.context_value(context, "base_path")
        if not project_path:
            return {"success": True, "output": {"updated": [], "skipped": True}}
        if not os.path.isdir(project_path):
            return {"success": False, "output": f"Project path not found: {project_path}"}

        goal = str(self.context_value(context, "goal", "Completed feature")).strip() or "Completed feature"
        updated = []
        try:
            updated.append(self._append_readme(project_path, goal))
            updated.append(self._append_changelog(project_path, goal))
            updated.append(self._write_feature_note(project_path, goal))
        except OSError as error:
            return {"success": False, "output": str(error), "error": str(error)}
        return {"success": True, "output": {"updated": updated}}

    @staticmethod
    def _append_readme(project_path, goal):
        path = os.path.join(project_path, "README.md")
        heading = "## Recent changes"
        existing = DocumentationAgent._read(path)
        addition = f"\n{heading}\n\n- {goal}\n"
        content = existing if heading in existing else existing.rstrip() + addition
        if heading in existing and f"- {goal}" not in existing:
            content = existing.rstrip() + f"\n- {goal}\n"
        DocumentationAgent._write(path, content)
        return path

    @staticmethod
    def _append_changelog(project_path, goal):
        path = os.path.join(project_path, "CHANGELOG.md")
        existing = DocumentationAgent._read(path)
        entry = f"## {date.today().isoformat()}\n\n- {goal}\n"
        if entry not in existing:
            DocumentationAgent._write(path, existing.rstrip() + ("\n\n" if existing.strip() else "") + entry)
        return path

    @staticmethod
    def _write_feature_note(project_path, goal):
        docs_path = os.path.join(project_path, "docs")
        os.makedirs(docs_path, exist_ok=True)
        path = os.path.join(docs_path, "latest-feature.md")
        DocumentationAgent._write(path, f"# Latest feature\n\n{goal}\n")
        return path

    @staticmethod
    def _read(path):
        if not os.path.isfile(path):
            return ""
        with open(path, "r", encoding="utf-8") as source:
            return source.read()

    @staticmethod
    def _write(path, content):
        with open(path, "w", encoding="utf-8") as destination:
            destination.write(content.rstrip() + "\n")
