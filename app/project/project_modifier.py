import ast
import json
import os

from app.ai.ai_manager import AIManager
from app.agent.file_manager import FileManager
from app.prompts.modifier_prompt import MODIFIER_PROMPT
from app.utils.json_utils import clean_json


class ProjectModifier:

    def __init__(self, analyzer):
        self.ai = AIManager()
        self.analyzer = analyzer
        self.files = FileManager()

    def modify(self, base_path, request):
        summary = self.analyzer.analyze(base_path)
        prompt = MODIFIER_PROMPT.format(request=request, summary=summary)
        response = clean_json(self.ai.ask(prompt))

        try:
            changes = json.loads(response).get("files", [])
        except (json.JSONDecodeError, AttributeError):
            return False, "Modifier returned invalid JSON"

        modified_files = []
        for change in changes:
            file_name = change.get("name", "")
            content = change.get("content")
            file_path = self._safe_path(base_path, file_name)
            if file_path is None or not isinstance(content, str):
                continue
            if file_name.endswith(".py"):
                try:
                    ast.parse(content, filename=file_name)
                except SyntaxError:
                    continue

            self.files.overwrite_file(file_path, content)
            modified_files.append(file_name)

        if not modified_files:
            return False, "No valid files were modified"

        return True, modified_files

    def _safe_path(self, base_path, file_name):
        if not file_name or os.path.isabs(file_name):
            return None

        project_root = os.path.abspath(base_path)
        file_path = os.path.abspath(os.path.join(project_root, file_name))
        if os.path.commonpath((project_root, file_path)) != project_root:
            return None

        return file_path
