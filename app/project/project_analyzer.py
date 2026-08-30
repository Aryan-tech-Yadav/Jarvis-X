import ast
import os


class ProjectAnalyzer:

    IGNORED_DIRECTORIES = {".git", ".venv", "venv", "__pycache__"}

    def analyze(self, base_path):
        summary = {
            "path": base_path,
            "files": [],
            "classes": [],
            "functions": [],
            "dependencies": [],
            "source": {},
            "requirements": "",
            "readme": "",
            "errors": [],
        }

        if not base_path or not os.path.isdir(base_path):
            summary["errors"].append("Project path not found")
            return summary

        dependencies = set()
        for root, directories, file_names in os.walk(base_path):
            directories[:] = [
                directory
                for directory in directories
                if directory not in self.IGNORED_DIRECTORIES
            ]

            for file_name in sorted(file_names):
                file_path = os.path.join(root, file_name)
                relative_path = os.path.relpath(file_path, base_path).replace(os.sep, "/")
                summary["files"].append(relative_path)

                if file_name == "requirements.txt":
                    summary["requirements"] = self._read_text(file_path, summary)
                elif file_name == "README.md":
                    summary["readme"] = self._read_text(file_path, summary)
                elif file_name.endswith(".py"):
                    source = self._read_text(file_path, summary)
                    summary["source"][relative_path] = source[:6000]
                    self._analyze_python_file(
                        source,
                        relative_path,
                        summary,
                        dependencies,
                    )

        summary["files"].sort()
        summary["dependencies"] = sorted(dependencies)
        return summary

    def _analyze_python_file(self, source, relative_path, summary, dependencies):
        try:
            tree = ast.parse(source, filename=relative_path)
        except SyntaxError as error:
            summary["errors"].append(f"Could not analyze {relative_path}: {error}")
            return

        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                target = "classes" if isinstance(node, ast.ClassDef) else "functions"
                summary[target].append({"name": node.name, "file": relative_path})
            elif isinstance(node, ast.Import):
                dependencies.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                dependencies.add(node.module.split(".")[0])

    def _read_text(self, file_path, summary):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        except (OSError, UnicodeDecodeError) as error:
            summary["errors"].append(f"Could not read {file_path}: {error}")
            return ""
