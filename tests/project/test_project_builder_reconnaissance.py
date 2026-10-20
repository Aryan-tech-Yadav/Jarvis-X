from unittest.mock import patch

from app.project.project_builder import ProjectBuilder


def test_default_builder_keeps_reconnaissance_disabled():
    with patch("app.project.project_builder.ProjectPlanner") as planner:
        ProjectBuilder()
        planner.assert_called_once_with(use_reconnaissance=False)


def test_builder_can_enable_reconnaissance():
    with patch("app.project.project_builder.ProjectPlanner") as planner:
        ProjectBuilder(use_reconnaissance=True)
        planner.assert_called_once_with(use_reconnaissance=True)
