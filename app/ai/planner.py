class TaskPlanner:
    
    def create_plan(self,command):
        
        command = command.lower()
        
        if "and" in command:
            
            return [
                step.strip()
                
                for step in command.split("and")
            ]
        
        return [command]