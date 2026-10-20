FIXER_PROMPT = """
You are an expert Python code reviewer.

Project:
{project}

Current File:
{file_name}

Current Code:
{code}

Improve this code.

Return complete runnable file content.
Preserve the file's public API and compatibility with other project files.
Do not remove required functions, classes, imports, or startup behavior.
Do not leave TODO markers, placeholder comments, or pass-only implementations.

Fix:
- syntax errors
- logic errors
- missing imports
- bad naming
- formatting
- edge cases

Return ONLY Python code.
Do not use markdown code fences.
Do not explain anything.
"""
