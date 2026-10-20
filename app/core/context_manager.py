class ContextManager:
    
    def __init__(self):
        self.last_app = None
        
    def set_last_app(self,app):
        self.last_app = app
        
    def get_last_app(self):
        return self.last_app