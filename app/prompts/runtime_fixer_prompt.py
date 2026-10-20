RUNTIME_FIXER_PROMPT = """
You are an expert Python developer.

The following file has a runtime error.

Project:
{project}

Current File:
{file_name}

Current Code:
{code}

Runtime Error:
{runtime_error}

Fix ONLY this file.

Return the complete corrected file, preserving all existing working behavior and public APIs.
Fix the reported error using the actual project structure and imports.
Do not replace the file with an explanation, apology, or partial snippet.
Do not change other files.

Return ONLY corrected Python code.

Do not use markdown.

Do not explain anything.
"""


def build_runtime_fixer_prompt(project, file_info, code, runtime_error):
    return RUNTIME_FIXER_PROMPT.format(
        project=project,
        file_name=file_info["name"],
        code=code,
        runtime_error=runtime_error,
    )
