"""Static checks for generated Python projects; never executes generated code."""
import ast
from pathlib import Path


class ProjectStaticValidator:
    def validate_project(self, base_path):
        root = Path(base_path).resolve()
        excluded = {".venv", "venv", "__pycache__", ".git"}
        paths = [
            p for p in root.rglob("*.py")
            if not any(part in excluded for part in p.relative_to(root).parts)
        ]

        modules, trees = {}, {}

        for path in paths:
            relative = path.relative_to(root)
            parts = list(relative.with_suffix("").parts)
            if parts[-1] == "__init__":
                parts.pop()
            if not parts:
                continue

            name = ".".join(parts)
            try:
                tree = ast.parse(
                    path.read_text(encoding="utf-8"),
                    filename=str(relative),
                )
            except (SyntaxError, UnicodeDecodeError, OSError) as error:
                return False, f"Syntax/read error in {relative}: {error}"

            modules[name] = path
            trees[name] = tree

        local_roots = {name.split(".")[0] for name in modules}
        exports = {}

        for name, tree in trees.items():
            names = set()
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    names.add(node.name)
                elif isinstance(node, ast.Assign):
                    names.update(
                        target.id for target in node.targets
                        if isinstance(target, ast.Name)
                    )
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    names.add(node.target.id)
                elif isinstance(node, ast.Import):
                    names.update(item.asname or item.name.split(".")[0] for item in node.names)
                elif isinstance(node, ast.ImportFrom):
                    names.update(
                        item.asname or item.name
                        for item in node.names if item.name != "*"
                    )
            exports[name] = names

        errors = []

        for name, tree in trees.items():
            path = modules[name]
            relative = path.relative_to(root)
            package_parts = name.split(".") if path.name == "__init__.py" else name.split(".")[:-1]

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for item in node.names:
                        target = item.name
                        if target.split(".")[0] in local_roots and target not in modules:
                            errors.append(
                                f"{relative}:{node.lineno}: local module '{target}' not found"
                            )

                elif isinstance(node, ast.ImportFrom):
                    target = node.module or ""

                    if node.level:
                        keep = len(package_parts) - node.level + 1
                        if keep < 0:
                            errors.append(f"{relative}:{node.lineno}: invalid relative import")
                            continue
                        resolved = package_parts[:keep]
                        if target:
                            resolved.extend(target.split("."))
                        target = ".".join(resolved)

                    if not target or target.split(".")[0] not in local_roots:
                        continue

                    if target not in modules:
                        errors.append(
                            f"{relative}:{node.lineno}: local module '{target}' not found"
                        )
                        continue

                    for item in node.names:
                        if item.name == "*":
                            continue
                        child = f"{target}.{item.name}"
                        if (
                            item.name not in exports.get(target, set())
                            and child not in modules
                        ):
                            errors.append(
                                f"{relative}:{node.lineno}: '{item.name}' not found "
                                f"in local module '{target}'"
                            )

        if errors:
            return False, "\n".join(errors)

        return True, f"Static validation passed: {len(trees)} Python files checked."
