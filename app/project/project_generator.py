import os
import shutil
from app.core.logger import Logger
from config import WORKSPACE

class ProjectGenerator:
    
    def __init__(self):
        pass
    
    def create_project(self, project, base_path=None):
        
        project_name = project["project_name"]
        
        if base_path is None:
            base_path = os.path.join(WORKSPACE, project_name)

        if os.path.exists(base_path):
            shutil.rmtree(base_path)
        
        
        for folder in project["folders"]:
            folder_path = os.path.join(base_path, folder)
            os.makedirs(folder_path, exist_ok=True)
            Logger.success(f"Folder created: {folder_path}")
            
        for file in project["files"]:
            file_path = os.path.join(base_path, file["name"])
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, "w", encoding="utf-8") as f:
                pass
            
        return base_path