import os
import re

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

            file_path = os.path.join(base_path, file_name)
            current_code = ""
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        current_code = file.read()
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

            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            self.files.overwrite_file(file_path, repaired_code)
            repaired_files.append(file_name)

        return repaired_files

    def _file_errors(self, validation_message):
        errors = {}
        for line in validation_message.splitlines():
            match = re.search(r"(?:Missing:|Empty file:|Syntax error in|Invalid import in)\s+([^:]+)", line)
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
        return (
            response.replace("```python", "")
            .replace("```markdown", "")
            .replace("```md", "")
            .replace("```", "")
            .strip()
        )
