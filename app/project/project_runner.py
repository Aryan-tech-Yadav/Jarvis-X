import os
import subprocess
import sys
from app.core.logger import Logger
from config import TIMEOUT


class ProjectRunner:

	def __init__(self, timeout=TIMEOUT):
		self.timeout = timeout

	def run(self, base_path):
		if not base_path:
			return False, "Invalid project path"

		entry_points = ("main.py", "app.py", "game.py")
		main_file = next(
			(
				os.path.abspath(os.path.join(base_path, entry_point))
				for entry_point in entry_points
				if os.path.exists(os.path.join(base_path, entry_point))
			),
			None,
		)
		Logger.info(f"Base Path: {base_path}")
		Logger.info(f"Main File: {main_file}")
		Logger.info(f"Exists: {main_file is not None and os.path.exists(main_file)}")

		if main_file is None:
			return False, "No runnable entry point found."

		try:
			Logger.info(f"Files: {os.listdir(base_path)}")
			result = subprocess.run(
				[sys.executable, main_file],
				cwd=base_path,
				capture_output=True,
				text=True,
				timeout=self.timeout,
			)
		except subprocess.TimeoutExpired:
			return False, f"Project timed out after {self.timeout} seconds"
		except OSError as error:
			return False, str(error)

		output = result.stdout.strip()
		error = result.stderr.strip()

		if result.returncode == 0:
			return True, output

		return False, error or output or f"Process exited with code {result.returncode}"
