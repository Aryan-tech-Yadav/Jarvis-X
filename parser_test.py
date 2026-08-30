from app.core.command_parser import CommandParser

parser = CommandParser()

tests = [
    
    "open notepad and calculator",
    
    "open paint, cmd",
    
    "open explorer then notepad",
]

for test in tests:
    
    print("=" * 40)
    print("Input :" , test)
    print("Output:", parser.split_commands(test))