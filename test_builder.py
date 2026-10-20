from app.project.project_builder import ProjectBuilder

builder = ProjectBuilder()

path = builder.build("Create Snake Game")

print(path)