import os
import subprocess
import shutil
from app.core.logger import Logger
from config import WORKSPACE

class FileManager:
    
    
    def save_python(self, filename, code):
        
        os.makedirs(WORKSPACE, exist_ok=True)
        
        path = os.path.abspath(os.path.join(WORKSPACE, filename))
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
            
        Logger.success(f"Saved: {path}")
          
        return path
    
    def open_in_vscode(self,path):
        code_path = shutil.which("code")
        
        vscode = r"C:\Users\fftec\AppData\Local\Programs\Microsoft VS Code\Code.exe"

        Logger.info(f"Opening: {path}")

        subprocess.Popen([vscode, path])
        
    #New Method 1
    def read_file(self, path):
        
        with open(path, "r" , encoding="utf-8") as f:
            return f.read()
    
    #New Method 2 
    
    def overwrite_file(self, path, code):
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
            
        Logger.success(f"Updated: {path}")