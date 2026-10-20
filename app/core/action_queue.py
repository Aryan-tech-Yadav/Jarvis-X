from collections import deque

class ActionQueue:
    
    def __init__(self):
        self.queue = deque()
        
    def add(self, action):
        self.queue.append(action)
        
    def get_next(self):
        
        if self.queue:
            return self.queue.popleft()
        
        return None
    
    def is_empty(self):
        return len(self.queue) ==0