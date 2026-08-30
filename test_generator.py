from app.project.project_generator import ProjectGenerator

project = {
    "project_name": "snake_game",
    "folders": [
        "src",
        "tests",
        "resources"
    ],
    "files": [
        {"name": "main.py", "type": "python"},
        {"name": "snake.py", "type": "python"},
        {"name": "game.py", "type": "python"}
    ]
}

generator = ProjectGenerator()

print(project)
path = generator.create_project(project)

print(path)