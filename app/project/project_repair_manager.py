import re
from pathlib import Path

from app.ai.ai_manager import AIManager
from app.agent.file_manager import FileManager
from app.project.project_tester import ProjectTester


class ProjectRepairManager:

    def __init__(self):
        self.ai = AIManager()
        self.files = FileManager()
        self.tester = ProjectTester()

    def repair(self, project, base_path, validation_message):
        repaired_files = []
        file_errors = self._file_errors(validation_message)

        repairable_files = list(project.get("files", []))
        for file_name, file_type in (("README.md", "markdown"), ("requirements.txt", "text")):
            if file_name in file_errors:
                repairable_files.append({"name": file_name, "type": file_type})

        for file_info in repairable_files:
            file_name = file_info.get("name", "")
            if file_name not in file_errors:
                continue

            try:
                file_path = self._resolve_project_path(base_path, file_name)
            except (ValueError, OSError):
                continue

            current_code = ""
            if file_path.is_file():
                try:
                    current_code = file_path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue

            prompt = self._build_prompt(
                project,
                file_info,
                current_code,
                file_errors[file_name],
            )
            response = self.ai.ask(prompt)
            repaired_code = self._clean_response(response)
            if not repaired_code:
                continue
            if file_name.endswith(".py"):
                passed, _ = self.tester.test(file_info, repaired_code)
                if not passed:
                    continue

            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(repaired_code, encoding="utf-8")
            except OSError:
                continue

            repaired_files.append(file_name)

        return repaired_files

    @staticmethod
    def _resolve_project_path(base_path, file_name):
        """Resolve a repair target and reject paths outside the project."""
        root = Path(base_path).expanduser().resolve()
        supplied = Path(file_name)

        if supplied.is_absolute():
            raise ValueError("Absolute repair paths are not allowed")

        target = (root / supplied).resolve()

        try:
            target.relative_to(root)
        except ValueError as exc:
            raise ValueError(
                "Repair path must remain inside the project"
            ) from exc

        if target == root:
            raise ValueError("Repair target must be a file inside the project")

        return target

    def _file_errors(self, validation_message):
        errors = {}
        for line in validation_message.splitlines():
            match = re.search(r"(?:Missing:|Empty file:|Syntax/read error in|Syntax error in|Invalid import in)\s+([^:]+)", line)
            if match:
                file_name = match.group(1).strip()
                errors.setdefault(file_name, []).append(line)
        return errors

    def _build_prompt(self, project, file_info, current_code, errors):
        file_type = file_info.get("type", "python")
        return f"""
You are an expert software engineer repairing one generated project file.

Project:
{project}

File to repair:
{file_info["name"]}

File type:
{file_type}

Current content:
{current_code}

Validation errors for this file:
{errors}

Repair ONLY this file.
Do not rewrite or modify any other project file.
Return ONLY the complete corrected file content.
Do not use markdown code fences.
Do not explain anything.
"""

    def _clean_response(self, response):
        if not isinstance(response, str):
            return ""

        return (
            response.replace("```python", "")
            .replace("```markdown", "")
            .replace("```md", "")
            .replace("```", "")
            .strip()
        )
