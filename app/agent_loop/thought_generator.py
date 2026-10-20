import json

from app.reasoning.json_parser import parse_thought


class ThoughtGenerator:
    def __init__(self, ai):
        self.ai = ai

    def generate(self, state):
        prompt = json.dumps({"goal": state.goal, "completed": state.history,
                             "instruction": "Return JSON only with thought, tool, action, arguments, finished."})
        return parse_thought(self.ai.ask(prompt), step=state.current_step + 1)