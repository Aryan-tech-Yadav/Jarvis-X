from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.project.project_builder import ProjectBuilder


def run_build(tmp_path, validation_results, repair_results):
    builder = ProjectBuilder.__new__(ProjectBuilder)

    builder.planner = MagicMock()
    builder.planner.plan.return_value = {
        "project_name": "test_project",
        "folders": ["tests"],
        "files": [{"name": "main.py", "content": "print('safe')"}],
    }

    builder.generator = MagicMock()
    builder.generator.create_project.return_value = str(tmp_path)
    builder.generate_files = MagicMock(return_value=[])

    builder.retry = SimpleNamespace(
        attempts=lambda: iter([0]),
        max_attempts=1,
    )

    builder.static_tester = MagicMock()
    builder.static_tester.validate_project.side_effect = validation_results

    builder.repair = MagicMock()
    builder.repair.repair.side_effect = repair_results

    builder.runner = MagicMock()
    builder.runner.run.return_value = (True, "mocked")

    builder.dependencies = MagicMock()
    builder.readme = MagicMock()
    builder.validator = MagicMock()
    builder.validator.validate.return_value = (True, "valid")
    builder.files = MagicMock()

    detection = SimpleNamespace(
        tech_stack=SimpleNamespace(template_id="test"),
        project_type=SimpleNamespace(value="test"),
    )

    with (
        patch(
            "app.engineering.project_type_detector.ProjectTypeDetector"
        ) as detector_class,
        patch("app.knowledge.template_store.TemplateRetriever"),
        patch(
            "app.knowledge.template_store.TemplateAugmentedGenerator"
        ) as template_generator_class,
    ):
        detector_class.return_value.detect.return_value = detection
        template_generator_class.return_value.generate_with_context.return_value = {
            "augmented": False,
            "files": [],
        }

        builder.build("Build a test project", base_path=str(tmp_path))

    return builder


def test_valid_project_runs_without_repair(tmp_path):
    builder = run_build(
        tmp_path,
        [(True, "Static validation passed")],
        [],
    )

    builder.repair.repair.assert_not_called()
    builder.runner.run.assert_called_once()


def test_project_runs_after_one_successful_repair(tmp_path):
    builder = run_build(
        tmp_path,
        [
            (False, "main.py:2: missing local symbol"),
            (True, "Static validation passed"),
        ],
        [["main.py"]],
    )

    builder.repair.repair.assert_called_once()
    builder.runner.run.assert_called_once()


def test_project_never_runs_after_two_failed_repairs(tmp_path):
    failure = (False, "main.py:2: missing local symbol")

    builder = run_build(
        tmp_path,
        [failure, failure, failure],
        [["main.py"], ["main.py"]],
    )

    assert builder.repair.repair.call_count == 2
    builder.runner.run.assert_not_called()
    assert builder.static_tester.validate_project.call_count == 3


def test_project_never_runs_when_repair_makes_no_changes(tmp_path):
    builder = run_build(
        tmp_path,
        [(False, "main.py:2: missing local symbol")],
        [[]],
    )

    builder.repair.repair.assert_called_once()
    builder.runner.run.assert_not_called()


def test_syntax_error_routes_to_correct_file_for_repair(tmp_path):
    builder = run_build(
        tmp_path,
        [
            (False, "Syntax/read error in main.py: invalid syntax"),
            (True, "Static validation passed"),
        ],
        [["main.py"]],
    )

    builder.repair.repair.assert_called_once_with(
        builder.planner.plan.return_value,
        str(tmp_path),
        "Syntax error in main.py: invalid syntax",
    )
    builder.runner.run.assert_called_once()
