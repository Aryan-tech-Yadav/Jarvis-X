class EntityExtractor:
    
    ALIASES = {
        "visual studio code": "vscode",
        "vs code": "vscode",
        "vscode": "vscode",
        
        "command prompt": "cmd",
        "cmd": "cmd",
        
        "file explorer": "explorer",
        "explorer": "explorer",
        
        "paint": "paint",
        "calculator": "calculator",
        "calc": "calculator",
        
        "notepad": "notepad",
        "task manager": "task manger"
        
    }
    
    def extract(self, text):
        
        text = text.lower()
        
        if text.startswith("what is my"):
            return text
        
        word = text.split()
        
        if len(word) <= 1:
            return None
        
        if text.startswith("who is"):
            return text.replace("who is", "").strip()
        if text.startswith("what is"):
            return text.replace("what is", "").strip()
        if text.startswith("tell me about"):
            return text.replace("tell me about", "").strip()
        if text.startswith("latest"):
            return text.replace("latest", "").strip()
        
        entity = " ".join(word[1:]).strip()
        
        return self.ALIASES.get(entity, entity)