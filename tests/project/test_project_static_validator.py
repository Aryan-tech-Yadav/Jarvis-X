from pathlib import Path

from app.project.project_static_validator import ProjectStaticValidator


def write_project(tmp_path: Path, files):
    for name, content in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return tmp_path


def test_accepts_valid_local_imports(tmp_path):
    root = write_project(tmp_path, {
        "main.py": "from calculator import add\nprint(add(1, 2))\n",
        "calculator/__init__.py": "from calculator.maths import add\n",
        "calculator/maths.py": "def add(a, b):\n    return a + b\n",
    })
    passed, message = ProjectStaticValidator().validate_project(root)
    assert passed, message


def test_rejects_missing_local_module(tmp_path):
    root = write_project(tmp_path, {
        "main.py": "from calculator.missing import add\n",
        "calculator/__init__.py": "",
    })
    passed, message = ProjectStaticValidator().validate_project(root)
    assert not passed
    assert "local module 'calculator.missing' not found" in message


def test_rejects_missing_imported_symbol(tmp_path):
    root = write_project(tmp_path, {
        "main.py": "from calculator.maths import subtract\n",
        "calculator/__init__.py": "",
        "calculator/maths.py": "def add(a, b):\n    return a + b\n",
    })
    passed, message = ProjectStaticValidator().validate_project(root)
    assert not passed
    assert "'subtract' not found" in message


def test_rejects_python_syntax_error(tmp_path):
    root = write_project(tmp_path, {"main.py": "def broken(:\n    pass\n"})
    passed, message = ProjectStaticValidator().validate_project(root)
    assert not passed
    assert "Syntax/read error" in message


def test_ignores_standard_library_imports(tmp_path):
    root = write_project(tmp_path, {"main.py": "import os\nimport json\n"})
    passed, message = ProjectStaticValidator().validate_project(root)
    assert passed, message
