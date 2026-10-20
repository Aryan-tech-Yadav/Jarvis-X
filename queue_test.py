from app.core.action_queue import ActionQueue

queue = ActionQueue()

queue.add("open notepad")
queue.add("open calculator")
queue.add("tell me a joke")

while not queue.is_empty():
    
    print(queue.get_next())