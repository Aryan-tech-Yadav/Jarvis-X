from collections import deque


class ReasoningActionQueue:
    def __init__(self):
        self.items = deque()

    def enqueue(self, action, priority=0):
        self.items.append((priority, action))
        self.items = deque(sorted(self.items, key=lambda item: item[0]))

    def dequeue(self):
        return self.items.popleft()[1] if self.items else None

    def cancel(self, action):
        self.items = deque(item for item in self.items if item[1] != action)