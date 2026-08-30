import json


def build_reasoning_prompt(goal, state, context=""):
    return json.dumps(
        {
            "goal": goal,
            "context": context,
            "step": state.current_step + 1,
            "thoughts": state.thoughts,
            "actions": state.actions,
            "observations": state.observations,
            "instruction": "Return JSON only: thought, tool, action, input, finished. No explanation outside JSON.",
        },
        ensure_ascii=True,
    )