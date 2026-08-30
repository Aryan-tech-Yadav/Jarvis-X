from app.ai.ai_manager import AIManager

class CodeGenerator:
    
    def __init__(self):
        self.ai = AIManager()
        
        
    def generate(self,prompt):
        
        full_prompt = f"""
        write complete Python code.
        
        Rules:
        
        - Return ONLY valid Python code.
        - Do NOT use markdown.
        - Do NOT use ```python
        - Do NOT use ```
        - Do NOT add explanations.
        - The output must be directly executable
        
        Task:
        {prompt}
        
        """
        
        response = self.ai.ask(full_prompt)
        
        #Remove markdown if AI still return it
        
        response = response.replace("'''python","")
        response = response.replace("'''Python","")
        response = response.replace("'''py","")
        response = response.replace("'''","")
        
        return response.strip()
        