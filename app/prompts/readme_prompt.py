README_PROMPT = """
You are an expert technical writer.

Create a professional README.md for this project.

Project Name:
{project_name}

Project Structure:
{project}

Generated Files:
{files}

Requirements:
{requirements}

Include these sections:
- Project overview
- Features
- Installation
- Usage
- Folder structure
- Notes

Use accurate information from the supplied project data.
If a detail is unknown, do not invent it.
Return ONLY Markdown content.
Do not wrap the response in code fences.
"""
