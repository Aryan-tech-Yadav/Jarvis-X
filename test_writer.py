
from app.project.project_planner import ProjectPlanner
from app.project.project_writer import ProjectWriter

planner = ProjectPlanner()

project = planner.plan("Create Snake Game")

writer = ProjectWriter()

code = writer.write_file(
    project,
    project["files"][0]
)

print(code)