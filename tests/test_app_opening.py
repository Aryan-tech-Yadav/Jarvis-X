"""Quick test for app/website opening capabilities."""

import unittest
from unittest.mock import patch, MagicMock

from app.core.hinglish_processor import HindiHinglishProcessor
from app.automation.website import WebsiteManager
from app.automation.application import ApplicationManager


class TestAppWebsiteOpening(unittest.TestCase):
    def setUp(self):
        self.processor = HindiHinglishProcessor()

    # Website opening tests
    def test_open_youtube_english(self):
        result = self.processor.parse("open youtube")
        self.assertEqual(result.intent, "OPEN_WEBSITE")
        self.assertIn("youtube", result.website_name.lower())

    def test_open_instagram_english(self):
        result = self.processor.parse("open instagram")
        self.assertEqual(result.intent, "OPEN_WEBSITE")
        self.assertIn("instagram", result.website_name.lower())

    def test_open_youtube_hindi(self):
        result = self.processor.parse("youtube खोलो")
        self.assertEqual(result.intent, "OPEN_WEBSITE")
        self.assertIn("youtube", result.website_name.lower())

    def test_open_instagram_hinglish(self):
        result = self.processor.parse("instagram kholo")
        self.assertEqual(result.intent, "OPEN_WEBSITE")
        self.assertIn("instagram", result.website_name.lower())

    def test_open_chrome_english(self):
        result = self.processor.parse("open chrome")
        self.assertEqual(result.intent, "OPEN_APPLICATION")
        self.assertIn("chrome", result.app_name.lower())

    def test_open_vscode_hinglish(self):
        result = self.processor.parse("vscode kholo")
        self.assertEqual(result.intent, "OPEN_APPLICATION")
        self.assertIn("vscode", result.app_name.lower())

    def test_open_notepad_hindi(self):
        result = self.processor.parse("notepad खोलो")
        self.assertEqual(result.intent, "OPEN_APPLICATION")
        self.assertIn("notepad", result.app_name.lower())

    def test_close_chrome_english(self):
        result = self.processor.parse("close chrome")
        self.assertEqual(result.intent, "CLOSE_APPLICATION")
        self.assertIn("chrome", result.app_name.lower())

    def test_close_app_hinglish(self):
        result = self.processor.parse("chrome band karo")
        self.assertEqual(result.intent, "CLOSE_APPLICATION")
        self.assertIn("chrome", result.app_name.lower())

    def test_visit_google_english(self):
        result = self.processor.parse("visit google")
        self.assertEqual(result.intent, "OPEN_WEBSITE")
        self.assertIn("google", result.website_name.lower())

    def test_go_to_youtube_english(self):
        result = self.processor.parse("go to youtube")
        self.assertEqual(result.intent, "OPEN_WEBSITE")
        self.assertIn("youtube", result.website_name.lower())

    def test_open_netflix_hinglish(self):
        result = self.processor.parse("netflix kholo")
        self.assertEqual(result.intent, "OPEN_WEBSITE")
        self.assertIn("netflix", result.website_name.lower())


class TestWebsiteManager(unittest.TestCase):
    def test_open_youtube(self):
        manager = WebsiteManager()
        with patch("webbrowser.open") as mock_open:
            result = manager.open("youtube")
            self.assertIn("Opening", result)
            mock_open.assert_called_once()

    def test_open_instagram(self):
        manager = WebsiteManager()
        with patch("webbrowser.open") as mock_open:
            result = manager.open("instagram")
            self.assertIn("Opening", result)
            mock_open.assert_called_once()

    def test_open_unknown_website(self):
        manager = WebsiteManager()
        with patch("webbrowser.open") as mock_open:
            result = manager.open("someunknownsite123")
            self.assertIn("Searching", result)
            mock_open.assert_called_once()


class TestApplicationManager(unittest.TestCase):
    def test_find_chrome_executable(self):
        manager = ApplicationManager()
        exe = manager._find_executable("chrome")
        self.assertIsNotNone(exe)

    def test_find_notepad_executable(self):
        manager = ApplicationManager()
        exe = manager._find_executable("notepad")
        self.assertIsNotNone(exe)


if __name__ == "__main__":
    unittest.main()
