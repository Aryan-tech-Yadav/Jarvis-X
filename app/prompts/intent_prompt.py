INTENT_PROMPT = """
Classify the user message for Jarvis-X.

Supported intents:
- CREATE_PROJECT: create or build a new project
- MODIFY_PROJECT: add, remove, fix, or change an existing project
- ANALYZE_PROJECT: inspect or explain the current project's structure
- GENERAL_CHAT: greetings or ordinary conversation
- HELP: asks how to use Jarvis
- EXIT: stop the CLI

Return ONLY valid JSON in this exact shape:
{{
    "intent": "CREATE_PROJECT",
    "request": "original user request"
}}

Rules:
- Choose exactly one supported intent.
- Preserve the user's complete request in request.
- Do not use markdown or explain anything.

User message:
{user_input}
"""
