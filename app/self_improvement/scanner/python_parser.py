"""Python AST parser for project analysis.

Parses Python source files using the standard library AST module
and extracts structural information:
  - classes, functions, methods
  - imports, decorators
  - async functions, global variables, constants
  - docstrings
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ParseError(Exception):
    """Raised when a file cannot be parsed."""


@dataclass
class FunctionInfo:
    """Information about a function or method."""

    name: str
    lineno: int
    end_lineno: int
    is_async: bool = False
    is_method: bool = False
    class_name: str = ""
    decorators: List[str] = field(default_factory=list)
    args_count: int = 0
    docstring: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "lineno": self.lineno,
            "end_lineno": self.end_lineno,
            "is_async": self.is_async,
            "is_method": self.is_method,
            "class_name": self.class_name,
            "decorators": list(self.decorators),
            "args_count": self.args_count,
            "docstring": self.docstring,
        }


@dataclass
class ClassInfo:
    """Information about a class definition."""

    name: str
    lineno: int
    end_lineno: int
    bases: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    methods: List[FunctionInfo] = field(default_factory=list)
    docstring: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "lineno": self.lineno,
            "end_lineno": self.end_lineno,
            "bases": list(self.bases),
            "decorators": list(self.decorators),
            "methods": [m.to_dict() for m in self.methods],
            "docstring": self.docstring,
        }


@dataclass
class ImportInfo:
    """Information about an import statement."""

    module: str
    alias: str = ""
    is_from: bool = False
    lineno: int = 0
    names: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "module": self.module,
            "alias": self.alias,
            "is_from": self.is_from,
            "lineno": self.lineno,
            "names": list(self.names),
        }


@dataclass
class FileAST:
    """Parsed AST information for a single file."""

    path: str
    content: str
    classes: List[ClassInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    imports: List[ImportInfo] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    async_functions: List[FunctionInfo] = field(default_factory=list)
    global_variables: List[str] = field(default_factory=list)
    constants: List[str] = field(default_factory=list)
    docstrings: List[str] = field(default_factory=list)
    tree: Optional[ast.AST] = None

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "classes": [c.to_dict() for c in self.classes],
            "functions": [f.to_dict() for f in self.functions],
            "imports": [i.to_dict() for i in self.imports],
            "decorators": list(self.decorators),
            "async_functions": [f.to_dict() for f in self.async_functions],
            "global_variables": list(self.global_variables),
            "constants": list(self.constants),
            "docstrings": list(self.docstrings),
        }


class PythonParser:
    """Parse Python source files using AST.

    Extracts structural information without using regex.
    """

    def __init__(self):
        self._tree_cache: Dict[str, FileAST] = {}

    def parse_file(self, path: str, content: str) -> FileAST:
        """Parse a single Python file.

        Args:
            path: Relative file path.
            content: File content string.

        Returns:
            FileAST with extracted information.

        Raises:
            ParseError: If file cannot be parsed.
        """
        if path in self._tree_cache:
            return self._tree_cache[path]

        try:
            tree = ast.parse(content, filename=path)
        except SyntaxError as exc:
            raise ParseError(f"Cannot parse {path}: {exc}") from exc

        file_ast = FileAST(path=path, content=content, tree=tree)
        self._extract_info(tree, file_ast)
        self._tree_cache[path] = file_ast
        return file_ast

    def parse_files(self, files: Dict[str, str]) -> Dict[str, FileAST]:
        """Parse multiple files.

        Args:
            files: Mapping of relative path to content.

        Returns:
            Mapping of relative path to FileAST.
        """
        results = {}
        for path, content in files.items():
            try:
                results[path] = self.parse_file(path, content)
            except ParseError:
                continue
        return results

    def _extract_info(self, tree: ast.AST, file_ast: FileAST):
        """Extract all structural information from AST."""
        # Module docstring
        module_docstring = ast.get_docstring(tree)
        if module_docstring:
            file_ast.docstrings.append(module_docstring)
        
        for node in ast.walk(tree):
            self._extract_class(node, file_ast)
            self._extract_function(node, file_ast)
            self._extract_import(node, file_ast)
            self._extract_decorator(node, file_ast)
            self._extract_global(node, file_ast)

    def _extract_class(self, node: ast.AST, file_ast: FileAST):
        """Extract class information."""
        if not isinstance(node, ast.ClassDef):
            return

        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{base.value.id}.{base.attr}" if isinstance(base.value, ast.Name) else "")

        decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        docstring = ast.get_docstring(node)

        class_info = ClassInfo(
            name=node.name,
            lineno=node.lineno,
            end_lineno=getattr(node, "end_lineno", node.lineno),
            bases=bases,
            decorators=decorators,
            docstring=docstring,
        )

        # Extract methods
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method = self._create_function_info(item, is_method=True, class_name=node.name)
                class_info.methods.append(method)
                file_ast.functions.append(method)
                if item not in [f for f in file_ast.functions]:
                    pass

        file_ast.classes.append(class_info)

    def _extract_function(self, node: ast.AST, file_ast: FileAST):
        """Extract function information."""
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        # Skip methods (already handled in _extract_class)
        if isinstance(node, ast.FunctionDef) and self._is_method(node):
            return

        func_info = self._create_function_info(node)
        file_ast.functions.append(func_info)
        if func_info.is_async:
            file_ast.async_functions.append(func_info)

    def _extract_import(self, node: ast.AST, file_ast: FileAST):
        """Extract import information."""
        if isinstance(node, ast.Import):
            for alias in node.names:
                file_ast.imports.append(ImportInfo(
                    module=alias.name,
                    alias=alias.asname or "",
                    is_from=False,
                    lineno=node.lineno,
                ))
        elif isinstance(node, ast.ImportFrom):
            names = [alias.name for alias in node.names]
            file_ast.imports.append(ImportInfo(
                module=node.module or "",
                is_from=True,
                lineno=node.lineno,
                names=names,
            ))

    def _extract_decorator(self, node: ast.AST, file_ast: FileAST):
        """Extract decorator information."""
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            for dec in node.decorator_list:
                name = self._get_decorator_name(dec)
                if name and name not in file_ast.decorators:
                    file_ast.decorators.append(name)

    def _extract_global(self, node: ast.AST, file_ast: FileAST):
        """Extract global variables and constants."""
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id
                    if name.isupper():
                        file_ast.constants.append(name)
                    elif not name.startswith("_"):
                        file_ast.global_variables.append(name)

    def _create_function_info(self, node: ast.FunctionDef | ast.AsyncFunctionDef,
                              is_method: bool = False, class_name: str = "") -> FunctionInfo:
        """Create FunctionInfo from AST node."""
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        docstring = ast.get_docstring(node)
        args_count = len(node.args.args) + len(node.args.posonlyargs) + len(node.args.kwonlyargs)

        return FunctionInfo(
            name=node.name,
            lineno=node.lineno,
            end_lineno=getattr(node, "end_lineno", node.lineno),
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_method=is_method,
            class_name=class_name,
            decorators=decorators,
            args_count=args_count,
            docstring=docstring,
        )

    @staticmethod
    def _is_method(node: ast.FunctionDef) -> bool:
        """Check if function is a method (has self/cls argument)."""
        if not node.args.args:
            return False
        first_arg = node.args.args[0].arg
        return first_arg in ("self", "cls")

    @staticmethod
    def _get_decorator_name(node: ast.AST) -> str:
        """Extract decorator name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node, ast.Attribute):
            parts = []
            current = node
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return ".".join(reversed(parts))
        return ""
