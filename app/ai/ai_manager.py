from app.ai.conversation_manager import ConversationManager
from app.ai.prompt_manager import SYSTEM_PROMPT
from app.llm.llm_router import LLMRouter

class AIManager:
    
    def __init__(self, router=None):
        
        self.chat = ConversationManager()
        self.router = router or LLMRouter()
        
        self.chat.messages.append({
            
            "role" : "system",
            "content" : SYSTEM_PROMPT
        })
        
        
    def ask(self, prompt, **kwargs):
        
        self.chat.add_user(prompt)
        
        answer = self.router.ask(
            prompt, messages=self.chat.get_messages(), **kwargs
        )
        
        self.chat.add_assistant(answer)
        
        return answer