from app.ai.ai_manager import AIManager
from app.core.logger import Logger
from app.utils.json_utils import clean_json
from app.prompts.designer_prompt import DESIGNER_PROMPT
import json


class ProjectDesigner:
    
    def __init__(self):
        self.ai = AIManager()
    
    def design(self, project, file):
        prompt = DESIGNER_PROMPT.format(
            project_name=project["project_name"],
            project=project,
            file_name=file["name"],
            file_type=file.get("type", "python"),
        )

        response = self.ai.ask(prompt)
        response = clean_json(response)

        try:
            return json.loads(response)
        except json.JSONDecodeError as error:
            Logger.error(f"Failed to parse project design JSON: {error}")
            return {
                "purpose":"",
                "classes":[],
                "functions":[],
                "imports":[],
                "dependencies":[],
                "notes": [],
                "public_api":[]
                
            }
        