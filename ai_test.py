from app.ai.ai_manager import AIManager

ai = AIManager()

while True:
    
    question = input("You: ")
    
    if question.lower() == "exit":
        
        break
    
    print()
    
    print("Jarvis:", ai.ask(question))
    
    print()