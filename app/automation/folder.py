import os

class FolderManager:
    
    def __init__(self):
        
        self.folder = {
            
            "downloads" : os.path.expanduser("~/Downloads"),
            
            "documents" : os.path.expanduser("~/Documents"),
            
            "desktop" : os.path.expanduser("~/Desktop"),
            
            "pictures" : os.path.expanduser("~/Pictures"),
            
            "music" : os.path.expanduser("~/Music")
            
        }
        
    def open(self, folder):
        
        folder = folder.lower().strip()
        
        if folder not in self.folders:
            
            return f"I don't know that folder."
        
        os.startfile(self.folders[folder])
        
        return f"Opening {folder}"