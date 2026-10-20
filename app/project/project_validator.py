import ast
import importlib.util
import os
import sys


class ProjectValidator:

    def __init__(self):
        self.standard_library = set(getattr(sys, "stdlib_module_names", set()))

    def validate(self, project, base_path):
        errors = []
        folders = project.get("folders", [])
        files = project.get("files", [])

        errors.extend(self._duplicate_entries(folders, "folder"))
        errors.extend(self._duplicate_entries([item.get("name", "") for item in files], "file"))

        for folder in folders:
            folder_path = os.path.join(base_path, folder)
            if folder.endswith(".py"):
                errors.append(f"Folder cannot be a Python file: {folder}")
            elif not os.path.isdir(folder_path):
                errors.append(f"Missing folder: {folder}")

        for file_info in files:
            file_name = file_info.get("name", "")
            file_path = os.path.join(base_path, file_name)
            if not os.path.isfile(file_path):
                errors.append(f"Missing: {file_name}")
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    code = file.read()
            except (OSError, UnicodeDecodeError) as error:
                errors.append(f"Unreadable file: {file_name} ({error})")
                continue

            if not code.strip():
                errors.append(f"Empty file: {file_name}")

            if file_name.endswith(".py"):
                try:
                    tree = ast.parse(code, filename=file_name)
                except SyntaxError as error:
                    errors.append(f"Syntax error in {file_name}: {error}")
                    continue
                errors.extend(self._invalid_imports(tree, file_name, base_path))

        for generated_file, label in (("README.md", "README"), ("requirements.txt", "requirements")):
            generated_path = os.path.join(base_path, generated_file)
            if os.path.isfile(generated_path):
                try:
                    with open(generated_path, "r", encoding="utf-8") as file:
                        if not file.read().strip():
                            errors.append(f"Empty file: {generated_file}")
                except (OSError, UnicodeDecodeError) as error:
                    errors.append(f"Unreadable file: {generated_file} ({error})")

        if not any(
            os.path.isfile(os.path.join(base_path, entry_point))
            for entry_point in ("main.py", "game.py", "app.py")
        ):
            errors.append("Project cannot run: main.py or game.py not found")

        if errors:
            return False, "\n".join(errors)
        return True, "Project validation passed"

    def _duplicate_entries(self, entries, entry_type):
        seen = set()
        duplicates = []
        for entry in entries:
            normalized = entry.replace("\\", "/").casefold()
            if normalized in seen and normalized not in duplicates:
                duplicates.append(normalized)
            seen.add(normalized)
        return [f"Duplicate {entry_type}: {entry}" for entry in duplicates]

    def _invalid_imports(self, tree, file_name, base_path):
        errors = []
        imported_modules = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imported_modules.append(node.module)

        for imported_module in imported_modules:
            module = imported_module.split(".")[0]
            if module in self.standard_library:
                continue
            if self._module_exists(imported_module, base_path):
                continue
            if importlib.util.find_spec(module) is None:
                errors.append(f"Invalid import in {file_name}: {imported_module}")
        return errors

    def _module_exists(self, module, base_path):
        module_path = module.replace(".", os.sep)
        return os.path.isfile(os.path.join(base_path, f"{module_path}.py")) or os.path.isfile(
            os.path.join(base_path, module_path, "__init__.py")
        )
