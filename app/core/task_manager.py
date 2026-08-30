from app.memory.memory_manager import MemoryManager
from app.core.logger import Logger
from app.automation.automation_manager import AutomationManager
from app.memory.memory_extractor import MemoryExtractor
from app.memory.query_extractor import QueryExctractor
from app.internet.internet_manager import InternetManager
from app.agent.code_generator import CodeGenerator
from app.agent.file_manager import FileManager
from app.agent.code_runner import CodeRunner
from app.agent.code_fixer import CodeFixer

class TaskManager:
    
    def __init__(self):
        self.automation = AutomationManager()
        self.memory = MemoryManager()
        self.extractor = MemoryExtractor()
        self.query = QueryExctractor()
        self.internet = InternetManager()
        self.generator = CodeGenerator()
        self.files = FileManager()
        self.runner = CodeRunner()
        self.fixer = CodeFixer()
    
    def execute(self , intent, entity, command=None):
        
        Logger.info(f"Excuting : {intent}") 
        
        if intent == "OPEN_APPLICATION":
            return self.automation.open_application(entity)
        
        elif intent == "GREETINGS":
            return "Hello Sir, NICE TO SEE YOU AGAIN."
        
        elif(intent) == "WEB_SEARCH":
            return self.internet.search_and_summarize(command)
        
        elif intent == "OPEN_WEBSITE":
            return self.internet.search_and_summarize(command)
        
        elif intent == "NEWS":
            return self.internet.get_news()

        elif intent == "WEATHER":
            return self.internet.get_weather(entity)

        elif intent == "WIKIPEDIA":
            return self.internet.wikipedia(entity)
        
        elif intent == "NEWS":
            return self.internet.get_news()
        
        elif intent == "CREATE_CODE":
            
            #Generate code
            code = self.generator.generate(command)
            
            #save
            filename = entity.replace(" ","_") + ".py"
            path = self.files.save_python(filename, code)
            
            #Open in VS Code 
            self.files.open_in_vscode(path)
            
            #Run Code
            Success, output = self.runner.run(path)
            
            #If Successful
            if Success:
                return f""" 
            Code generated Successfully.
            
            Saved at:
            {path}
            
            Program Output:
            {output}
            """
            #If failed -> Ask AI to fix
            fixed_code = self.fixer.fix(code, output)
            
            #Save fixed code
            self.files.overwrite_file(path, fixed_code)
            
            #Run again
            Success, output = self.runner.run(path)

            
            if Success:
                
                return f"""
            Code generated Successfully.
            
            AI detected an error.
            
            The code was automatically fixed.
            
            Saved at:
            {path}
            
            Program Output:
            
            {output}
            """
            return f"""
        
        Jarvis tried to fix the code but it still failed.
        
        Error:
        
        {output}
        
        """
        
            
        
        elif intent == "OPEN_FOLDER":
            return self.automation.open_folder(entity)
        
        elif intent == "OPEN_MUSIC":
            return self.automation.play_music()
        
        elif intent == "GET_TIME":
            return "Sure Sir, checking the current time."
                
        elif intent == "SAVE_MEMORY":
            
            key, value = self.extractor.extract(entity)
            
            if key and value:
                
                #name = entity.replace("my name is", "").strip()               
                self.memory.save_memory(key, value)
                return f"Okay Sir, I'll remember your{key.replace('_', ' ')}."
            
            return "I couldn't understand what to remember."
        
        elif intent == "GET_MEMORY":
            
            key = self.query.extract(command)
            
            if key:
                
                value = self.memory.get_memory(key)
                
                if value:
                    return f"Your {key.replace('_', ' ')} is {value}."
                
            return "I don't remember that yet."
            
        
        elif intent == "CLOSE_APPLICATION":
            return self.automation.close_application(entity)
                         
        elif intent == "EXIT":
            return "Shutting Down..."
               
        else:
            return "Soory Sir, I don't know to do that yet."      