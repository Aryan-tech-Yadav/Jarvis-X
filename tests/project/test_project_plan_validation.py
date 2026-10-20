import pytest

from app.project.project_planner import ProjectPlanner


def valid_plan():
    return {
        "project_name": "demo_app",
        "folders": ["src", "tests"],
        "files": [
            {"name": "src/main.py", "type": "python"},
            {"name": "tests/test_main.py", "type": "python"},
            {"name": "README.md", "type": "txt"},
        ],
    }


def test_valid_plan_is_accepted():
    assert ProjectPlanner._validate_plan(valid_plan()) is None


@pytest.mark.parametrize(
    "bad_path",
    ["../outside.py", "/tmp/outside.py", "src/../outside.py"],
)
def test_unsafe_file_paths_are_rejected(bad_path):
    plan = valid_plan()
    plan["files"][0]["name"] = bad_path
    assert "Unsafe file path" in ProjectPlanner._validate_plan(plan)


def test_duplicate_file_paths_are_rejected():
    plan = valid_plan()
    plan["files"].append(dict(plan["files"][0]))
    assert "Duplicate file path" in ProjectPlanner._validate_plan(plan)


def test_duplicate_folders_are_rejected():
    plan = valid_plan()
    plan["folders"].append("src")
    assert "Duplicate folder path" in ProjectPlanner._validate_plan(plan)


def test_undeclared_nested_parent_is_rejected():
    plan = valid_plan()
    plan["files"][0]["name"] = "src/utils/helper.py"
    assert "File parent folder is not declared" in (
        ProjectPlanner._validate_plan(plan)
    )


def test_root_level_files_are_allowed():
    plan = valid_plan()
    plan["files"] = [
        {"name": "main.py", "type": "python"},
        {"name": "README.md", "type": "txt"},
    ]
    assert ProjectPlanner._validate_plan(plan) is None


def test_missing_test_file_is_not_a_schema_error():
    plan = valid_plan()
    plan["files"] = [
        {"name": "src/main.py", "type": "python"},
        {"name": "README.md", "type": "txt"},
    ]
    assert ProjectPlanner._validate_plan(plan) is None
