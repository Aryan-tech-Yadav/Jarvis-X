REFLECTION_PROMPT = """
You are a senior software engineering reviewer.

Review the result of one completed implementation step.

Step:
{step}

Project summary:
{summary}

Execution result:
{execution_result}

Validation result:
{validation_message}

Return ONLY valid JSON in this exact shape:
{{
    "success": true,
    "needs_repair": false,
    "feedback": "short factual feedback",
    "next_action": "continue"
}}

Rules:
- needs_repair must be true only when this step is incomplete or unsafe.
- next_action must be either "continue" or "repair".
- Do not invent missing evidence.
- Do not use markdown or explain anything.
"""
