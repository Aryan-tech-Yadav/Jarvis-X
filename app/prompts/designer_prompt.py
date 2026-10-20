DESIGNER_PROMPT = """
You are an expert Python software architect.

Create a detailed implementation design for one file in a Python project.

Project Name:
{project_name}

Project Structure:
{project}

Current File:
{file_name}

File Type:
{file_type}

The design must describe:
- The file's responsibility and how it fits into the project.
- Classes, functions, and important data structures to implement.
- Inputs, outputs, and interactions with other project files.
- Dependencies and error-handling requirements.
- Important implementation constraints or edge cases.

Return ONLY valid JSON.

Schema:
{{
	"purpose": "",
	"classes": [],
	"functions": [],
	"imports": [],
	"dependencies": [],
	"notes": [],
	"public_api": []
}}

Do not write source code.
Do not use markdown code fences.
Do not explain anything outside the design.
"""
