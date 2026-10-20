import os

from app.ai.ai_manager import AIManager
from app.prompts.readme_prompt import README_PROMPT


class ProjectReadmeGenerator:

    def __init__(self):
        self.ai = AIManager()

    def generate(self, project, base_path):
        requirements_path = os.path.join(base_path, "requirements.txt")
        requirements = ""
        if os.path.isfile(requirements_path):
            with open(requirements_path, "r", encoding="utf-8") as file:
                requirements = file.read().strip()

        files = []
        for root, directories, file_names in os.walk(base_path):
            directories[:] = [d for d in directories if d not in {".git", ".venv", "venv", "__pycache__", "node_modules"}]
            for file_name in file_names:
                relative_path = os.path.relpath(
                    os.path.join(root, file_name),
                    base_path,
                )
                files.append(relative_path.replace(os.sep, "/"))

        prompt = README_PROMPT.format(
            project_name=project.get("project_name", ""),
            project=project,
            files="\n".join(sorted(files)),
            requirements=requirements or "No external dependencies.",
        )
        response = self.ai.ask(prompt)
        response = response.replace("```markdown", "")
        response = response.replace("```md", "")
        response = response.replace("```", "")

        readme_path = os.path.join(base_path, "README.md")
        with open(readme_path, "w", encoding="utf-8") as file:
            file.write(response.strip() + "\n")

        return readme_path
