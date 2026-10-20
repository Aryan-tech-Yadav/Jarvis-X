import ast
import os
import subprocess
import sys


class ProjectDependencyManager:

    def __init__(self):
        self.standard_library = set(getattr(sys, "stdlib_module_names", set()))

    def scan(self, base_path):
        dependencies = set()
        local_modules = self._local_modules(base_path)

        for root, directories, files in os.walk(base_path):
            directories[:] = [d for d in directories if d not in {".git", ".venv", "venv", "__pycache__", "node_modules"}]
            for file_name in files:
                if not file_name.endswith(".py"):
                    continue

                file_path = os.path.join(root, file_name)
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        tree = ast.parse(file.read(), filename=file_path)
                except (OSError, UnicodeDecodeError, SyntaxError):
                    continue

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        dependencies.update(alias.name.split(".")[0] for alias in node.names)
                    elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                        dependencies.add(node.module.split(".")[0])

        return sorted(
            dependency
            for dependency in dependencies
            if dependency not in self.standard_library and dependency not in local_modules
        )

    def _local_modules(self, base_path):
        modules = set()

        for root, directories, files in os.walk(base_path):
            directories[:] = [d for d in directories if d not in {".git", ".venv", "venv", "__pycache__", "node_modules"}]
            for file_name in files:
                if file_name.endswith(".py"):
                    modules.add(file_name[:-3])
            for directory in directories:
                if os.path.isfile(os.path.join(root, directory, "__init__.py")):
                    modules.add(directory)

        return modules

    def generate_requirements(self, base_path):
        dependencies = self.scan(base_path)
        requirements_path = os.path.join(base_path, "requirements.txt")

        with open(requirements_path, "w", encoding="utf-8") as file:
            file.write("\n".join(dependencies))
            if dependencies:
                file.write("\n")

        return requirements_path

    def install(self, base_path):
        requirements_path = os.path.join(base_path, "requirements.txt")
        if not os.path.isfile(requirements_path):
            return False, "requirements.txt not found"

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", requirements_path],
                cwd=base_path,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as error:
            return False, str(error)

        if result.returncode == 0:
            return True, result.stdout.strip()

        return False, result.stderr.strip() or result.stdout.strip()
