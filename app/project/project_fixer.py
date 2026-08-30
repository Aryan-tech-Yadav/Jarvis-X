
from app.project.project_planner import ProjectPlanner
from app.project.project_generator import ProjectGenerator
from app.project.project_designer import ProjectDesigner
from app.project.project_writer import ProjectWriter
from app.ai.ai_manager import AIManager
from app.prompts.fixer_prompt import FIXER_PROMPT

class ProjectFixer:

    def __init__(self):
        self.planner = ProjectPlanner()
        self.generator = ProjectGenerator()
        self.designer = ProjectDesigner()
        self.writer = ProjectWriter()
        self.ai = AIManager()

    def fix(self, project, file_info, code):
        prompt = FIXER_PROMPT.format(
            project=project,
            file_name=file_info["name"],
            code=code,
        )

        response = self.ai.ask(prompt)
        response = response.replace("```python", "")
        response = response.replace("```py", "")
        response = response.replace("```", "")
        return response.strip()
        