"""Tests for system control and music playback features."""

import unittest
from unittest.mock import patch, MagicMock

from app.core.hinglish_processor import HindiHinglishProcessor
from app.automation.automation_manager import AutomationManager


class TestSystemControlIntents(unittest.TestCase):
    def setUp(self):
        self.processor = HindiHinglishProcessor()

    def test_shutdown_english(self):
        result = self.processor.parse("shutdown my laptop")
        self.assertEqual(result.intent, "SHUTDOWN")

    def test_shutdown_hindi(self):
        result = self.processor.parse("शटडाउन करो")
        self.assertEqual(result.intent, "SHUTDOWN")

    def test_shutdown_hinglish(self):
        result = self.processor.parse("band ho ja")
        self.assertEqual(result.intent, "SHUTDOWN")

    def test_restart_english(self):
        result = self.processor.parse("restart laptop")
        self.assertEqual(result.intent, "RESTART")

    def test_restart_hinglish(self):
        result = self.processor.parse("restart karo")
        self.assertEqual(result.intent, "RESTART")

    def test_sleep_english(self):
        result = self.processor.parse("sleep mode")
        self.assertEqual(result.intent, "SLEEP")

    def test_sleep_hinglish(self):
        result = self.processor.parse("so ja")
        self.assertEqual(result.intent, "SLEEP")

    def test_lock_english(self):
        result = self.processor.parse("lock screen")
        self.assertEqual(result.intent, "LOCK")

    def test_lock_hinglish(self):
        result = self.processor.parse("lock karo")
        self.assertEqual(result.intent, "LOCK")

    def test_cancel_shutdown_english(self):
        result = self.processor.parse("cancel shutdown")
        self.assertEqual(result.intent, "CANCEL_SHUTDOWN")

    def test_cancel_restart_english(self):
        result = self.processor.parse("cancel restart")
        self.assertEqual(result.intent, "CANCEL_SHUTDOWN")

    def test_power_off_synonym(self):
        result = self.processor.parse("power off")
        self.assertEqual(result.intent, "SHUTDOWN")

    def test_turn_off_synonym(self):
        result = self.processor.parse("turn off laptop")
        self.assertEqual(result.intent, "SHUTDOWN")


class TestMusicPlaybackIntents(unittest.TestCase):
    def setUp(self):
        self.processor = HindiHinglishProcessor()

    def test_play_music_english(self):
        result = self.processor.parse("play music")
        self.assertEqual(result.intent, "PLAY_MUSIC")

    def test_play_spotify_english(self):
        result = self.processor.parse("play spotify")
        self.assertEqual(result.intent, "PLAY_MUSIC")

    def test_start_music_english(self):
        result = self.processor.parse("start music")
        self.assertEqual(result.intent, "PLAY_MUSIC")

    def test_music_play_hinglish(self):
        result = self.processor.parse("music play karo")
        self.assertEqual(result.intent, "PLAY_MUSIC")

    def test_gaana_bajao_hindi(self):
        result = self.processor.parse("गाना बजाओ")
        self.assertEqual(result.intent, "PLAY_MUSIC")

    def test_gaana_bajao_hinglish(self):
        result = self.processor.parse("gaana bajao")
        self.assertEqual(result.intent, "PLAY_MUSIC")

    def test_spotify_chalao_hinglish(self):
        result = self.processor.parse("spotify chalao")
        self.assertEqual(result.intent, "PLAY_MUSIC")

    def test_play_song_on_spotify_english(self):
        result = self.processor.parse("play shape of you on spotify")
        self.assertEqual(result.intent, "PLAY_SPOTIFY_SONG")
        self.assertIn("shape of you", result.song_name.lower())

    def test_spotify_pe_song_hinglish(self):
        result = self.processor.parse("spotify pe shape of you chalao")
        self.assertEqual(result.intent, "PLAY_SPOTIFY_SONG")
        self.assertIn("shape of you", result.song_name.lower())

    def test_play_tum_hi_ho_spotify(self):
        result = self.processor.parse("play tum hi ho on spotify")
        self.assertEqual(result.intent, "PLAY_SPOTIFY_SONG")
        self.assertIn("tum hi ho", result.song_name.lower())


class TestNewsAndSearchIntents(unittest.TestCase):
    def setUp(self):
        self.processor = HindiHinglishProcessor()

    def test_news_english(self):
        result = self.processor.parse("latest news")
        self.assertEqual(result.intent, "GET_NEWS")

    def test_news_hindi(self):
        result = self.processor.parse("ताजा खबरें")
        self.assertEqual(result.intent, "GET_NEWS")

    def test_news_hinglish(self):
        result = self.processor.parse("khabar bataye")
        self.assertEqual(result.intent, "GET_NEWS")

    def test_tech_news(self):
        result = self.processor.parse("tech news")
        self.assertEqual(result.intent, "GET_NEWS")

    def test_google_search_english(self):
        result = self.processor.parse("google python tutorials")
        self.assertEqual(result.intent, "GOOGLE_SEARCH")
        self.assertIn("python tutorials", result.search_query.lower())

    def test_google_search_hinglish(self):
        result = self.processor.parse("google pe Jarvis-X search karo")
        self.assertEqual(result.intent, "GOOGLE_SEARCH")
        self.assertIn("jarvis-x", result.search_query.lower())

    def test_search_english(self):
        result = self.processor.parse("search how to make website")
        self.assertEqual(result.intent, "GOOGLE_SEARCH")
        self.assertIn("how to make website", result.search_query.lower())


class TestAutomationManagerSystemControls(unittest.TestCase):
    def setUp(self):
        self.manager = AutomationManager()

    @patch("subprocess.run")
    def test_shutdown_calls_subprocess(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        result = self.manager.shutdown()
        self.assertIn("shutdown", result.lower())
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_restart_calls_subprocess(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        result = self.manager.restart()
        self.assertIn("restart", result.lower())
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_cancel_shutdown_calls_subprocess(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        result = self.manager.cancel_shutdown()
        self.assertIn("cancel", result.lower())
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_lock_calls_rundll32(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        result = self.manager.lock()
        self.assertIn("lock", result.lower())
        mock_run.assert_called_once()

    @patch("app.automation.automation_manager.ApplicationManager.open")
    def test_play_spotify_opens_spotify(self, mock_open):
        mock_open.return_value = "Opening spotify."
        result = self.manager.play_spotify()
        mock_open.assert_called_once_with("spotify")


if __name__ == "__main__":
    unittest.main()
