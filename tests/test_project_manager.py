import unittest
from unittest.mock import patch

from app.project.project_manager import ProjectManager


class ProjectManagerValidationTests(unittest.TestCase):
    def test_validate_rejects_missing_project_path(self):
        manager = ProjectManager()

        valid, message = manager.validate_project("missing_project")

        self.assertFalse(valid)
        self.assertIn("Project path not found", message)

    def test_modify_rejects_missing_project_path_without_calling_modifier(self):
        manager = ProjectManager()

        with patch.object(manager.modifier, "modify") as mock_modify:
            success, result = manager.modify_project("missing_project", "Add a README")

        self.assertFalse(success)
        self.assertIn("Project path not found", result)
        mock_modify.assert_not_called()


if __name__ == "__main__":
    unittest.main()
