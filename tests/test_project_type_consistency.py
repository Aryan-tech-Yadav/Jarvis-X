import unittest

from app.engineering.architecture_designer import ArchitectureDesigner
from app.engineering.project_type_detector import ProjectType, ProjectTypeDetector
from app.engineering.requirement_analyzer import RequirementAnalyzer


class TestProjectTypeConsistency(unittest.TestCase):
    def test_tic_tac_toe_remains_a_game_across_analysis_and_detection(self):
        prompt = "Build a tic tac toe game"

        detection = ProjectTypeDetector().detect(prompt, use_llm=False)
        analysis = RequirementAnalyzer().analyze(prompt)

        self.assertEqual(detection.project_type, ProjectType.GAME)
        self.assertEqual(analysis.project_type, "game")
        self.assertEqual(analysis.frontend, "Pygame")

    def test_game_architecture_does_not_use_web_layers(self):
        layers = ArchitectureDesigner()._select_layers("game")

        self.assertEqual(layers, ["Game Loop", "Input", "Rendering", "Game State", "Audio"])
        self.assertNotIn("Database", layers)

    def test_management_word_does_not_trigger_game_detection(self):
        prompt = "Build a hospital management system"

        detection = ProjectTypeDetector().detect(prompt, use_llm=False)
        analysis = RequirementAnalyzer().analyze(prompt)

        self.assertNotEqual(detection.project_type, ProjectType.GAME)
        self.assertNotEqual(analysis.project_type, "game")


if __name__ == "__main__":
    unittest.main()
