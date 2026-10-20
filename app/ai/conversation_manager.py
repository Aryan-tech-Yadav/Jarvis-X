class ConversationManager:
    
    def __init__(self):
        
        self.messages = []
        
    def add_user(self, text):
       
       self.messages.append({
           
           "role" : "user",
           "content" : text
       })
       
       
    def add_assistant(self, text):
         
         self.messages.append({
             
             "role" : "assistant",
             "content" : text
         })
         
    def get_messages(self):
        
        return self.messages
    
    def clear(self):
        
        self.messages.clear()