from app.ai.ai_manager import AIManager
from app.prompts.runtime_fixer_prompt import build_runtime_fixer_prompt


class ProjectRuntimeFixer:

	def __init__(self):
		self.ai = AIManager()

	def fix(self, project, file_info, code, runtime_error):
		prompt = build_runtime_fixer_prompt(
			project,
			file_info,
			code,
			runtime_error,
		)

		response = self.ai.ask(prompt)
		response = response.replace("```python", "")
		response = response.replace("```", "")

		return response.strip()
