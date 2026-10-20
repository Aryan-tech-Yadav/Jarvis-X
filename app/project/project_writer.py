from app.ai.ai_manager import AIManager
from app.agent.file_manager import FileManager
from app.prompts.writer_prompt import WRITER_PROMPT

class ProjectWriter:
    
    def __init__(self):
        
        self.ai = AIManager()
        self.files = FileManager()
        
    def write_file(self, project, file, design, context=""):
        prompt = WRITER_PROMPT.format(
            project_name=project["project_name"],
            project=project,
            file_name=file["name"],
            file_type=file.get("type", "python"),
            design=design,
            context=context,
        )
        
        response = self.ai.ask(prompt)
        
        response = response.replace("```python", "")
        response = response.replace("```py", "")
        response = response.replace("```", "")
        response = response.strip()
        
        
        return response