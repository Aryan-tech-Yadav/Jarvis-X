"""Tests for Jarvis voice system."""

import unittest
from unittest.mock import patch, MagicMock

from app.voice.jarvis_voice import JarvisVoice
from app.core.hinglish_processor import HindiHinglishProcessor


class TestJarvisVoice(unittest.TestCase):
    def test_voice_initialization(self):
        voice = JarvisVoice()
        self.assertIsNotNone(voice)

    def test_speak_with_speaker(self):
        voice = JarvisVoice()
        with patch.object(voice, '_speaker') as mock_speaker:
            voice.speak("Hello, I am Jarvis.")
            mock_speaker.say.assert_called_once_with("Hello, I am Jarvis.")

    def test_speak_with_none_text(self):
        voice = JarvisVoice()
        # Should not raise
        voice.speak("")
        voice.speak(None)

    def test_configure_jarvis_voice(self):
        voice = JarvisVoice()
        with patch.object(voice, '_speaker') as mock_speaker:
            mock_speaker.getProperty.return_value = []
            voice._configure_jarvis_voice()
            # Should not raise

    def test_set_voice_speed(self):
        voice = JarvisVoice()
        with patch.object(voice, '_speaker') as mock_speaker:
            voice.set_voice_speed(150)
            mock_speaker.setProperty.assert_called()

    def test_set_voice_volume(self):
        voice = JarvisVoice()
        with patch.object(voice, '_speaker') as mock_speaker:
            voice.set_voice_volume(0.8)
            mock_speaker.setProperty.assert_called()

    def test_listen_without_components(self):
        voice = JarvisVoice()
        voice._recorder = None
        voice._transcriber = None
        result = voice.listen()
        self.assertIsNone(result)

    def test_wake_word_detection_patterns(self):
        """Test that wake word 'Jarvis' is recognized in various inputs."""
        processor = HindiHinglishProcessor()
        tests = [
            ("hey jarvis open youtube", "OPEN_WEBSITE"),
            ("jarvis shutdown laptop", "SHUTDOWN"),
            ("jarvis play music", "PLAY_MUSIC"),
            ("jarvis banao hospital", "CREATE_CODE"),
        ]
        for text, expected_intent in tests:
            result = processor.parse(text)
            self.assertEqual(result.intent, expected_intent, f"Failed for: {text}")


if __name__ == "__main__":
    unittest.main()
