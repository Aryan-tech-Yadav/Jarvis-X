class CommandParser:
    
    def split_commands(self,text):
        
        separators = [
            
            "and",
            
            "then",
            
            ", "
        ]
        
        commands = [text]
        
        for separator in separators:
            
            temp = []
            
            for command in commands:
                
                if separator == "and":
                    temp.extend(command.split(" and "))
                    
                elif separator == "then":
                    temp.extend(command.split(" then "))
                    
                else:
                    temp.extend(command.split(","))
                
            commands = temp
        commands = [cmd.strip() for cmd in commands if cmd.strip()]
        
        if len(commands) > 1:
            
            first_words = commands[0].split()
            
            action = first_words[0]
            
            for i in range(1, len(commands)):
                
                if len(commands[i].split()) ==1:
                    commands[i] = action + " " + commands[i]
            
        return commands 
        