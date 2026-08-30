from app.ai.ai_manager import AIManager

class CodeFixer:
    
    def __init__(self):
        self.ai = AIManager()
        
    def fix(self,code,error):
        prompt = f"""
        
        You are an expert Python developer.
        
        Your task is to fix the Python code.
        
        Rules:
        -Return ONLY valid Python code.
        -Do NOT use markdown.
        -Do NOT use '''python.
        -Do NOT  explain anything.
        -Preserve the original functionality unless requried to fix the error.
        
        Original Code:
        
        {code}
        
        Python Error:
        
        {error}
        """
        return self.ai.ask(prompt)
        