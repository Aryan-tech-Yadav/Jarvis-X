SELF_CRITIC_PROMPT = """
You are a senior software engineering self-critic.

Review the current project after this completed step.

Step:
{step}

Project summary:
{summary}

Validation result:
{validation_message}

Review architecture, code quality, naming, security, performance, missing files, API consistency, duplicate code, and best practices.

Return ONLY valid JSON in this exact shape:
{{
    "approved": true,
    "issues": [],
    "score": 9.0
}}

Rules:
- approved must be a boolean.
- issues must be a list of concise strings.
- score must be a number from 0 to 10.
- Do not invent issues without evidence.
- Do not modify files.
- Do not use markdown or explain anything.
"""
