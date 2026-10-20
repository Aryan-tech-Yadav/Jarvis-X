from app.ai.planner import TaskPlanner

planner = TaskPlanner()

plan = planner.create_plan(
    "open notepad and open calculator"  
)

print(plan)