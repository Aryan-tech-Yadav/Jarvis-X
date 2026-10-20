WRITER_PROMPT = """
You are an expert Python developer.

Project Name:
{project_name}

Project Structure:
{project}

Current File:
{file_name}

File Type:
{file_type}

File Design:
{design}

Context From Other Project Files:
{context}

Write ONLY the code for this file.

Return complete content, not a sketch or partial snippet.
Implement every function and public API described in the design.
Use imports and names that match the project context exactly.
For Python entry points, include executable startup code.
Do not use TODO markers, placeholder comments, or empty pass-only implementations.
Do not reference files, classes, functions, or settings that are not present in the project context.
Do not write markdown.
Do not use triple backticks or triple quotes as code fences.
Do not explain anything.
"""
