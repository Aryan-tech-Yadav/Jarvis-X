"""Tests for Hindi/Hinglish language processor."""

import unittest

from app.core.hinglish_processor import HindiHinglishProcessor, HinglishResponseGenerator, ParsedIntent


class TestHindiHinglishProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = HindiHinglishProcessor()

    def test_parse_english_create_code(self):
        result = self.processor.parse("Build hospital management system")
        self.assertEqual(result.intent, "CREATE_CODE")
        self.assertGreater(result.confidence, 0.8)
        self.assertIn("hospital", result.domain)

    def test_parse_hindi_create_code(self):
        result = self.processor.parse("बनाओ hospital management system")
        self.assertEqual(result.intent, "CREATE_CODE")

    def test_parse_hinglish_create_code(self):
        result = self.processor.parse("banao hospital management system")
        self.assertEqual(result.intent, "CREATE_CODE")

    def test_parse_hindi_hinglish_mixed(self):
        result = self.processor.parse("ek hospital management system banao")
        self.assertEqual(result.intent, "CREATE_CODE")

    def test_parse_status_english(self):
        result = self.processor.parse("status")
        self.assertEqual(result.intent, "STATUS")

    def test_parse_status_hindi(self):
        result = self.processor.parse("क्या हुआ")
        self.assertEqual(result.intent, "STATUS")

    def test_parse_history(self):
        result = self.processor.parse("pehle ka project dikhao")
        self.assertEqual(result.intent, "HISTORY")

    def test_parse_help(self):
        result = self.processor.parse("help")
        self.assertEqual(result.intent, "HELP")

    def test_parse_exit(self):
        result = self.processor.parse("exit")
        self.assertEqual(result.intent, "EXIT")

    def test_parse_chat(self):
        result = self.processor.parse("hello jarvis")
        self.assertEqual(result.intent, "CHAT")

    def test_extract_project_name_english(self):
        result = self.processor.parse("Build hospital management system")
        self.assertIn("hospital", result.project_name.lower())

    def test_extract_project_name_hindi(self):
        result = self.processor.parse("hospital management system बनाओ")
        self.assertIn("hospital", result.project_name.lower())

    def test_extract_project_name_hinglish(self):
        result = self.processor.parse("hospital management system banao")
        self.assertIn("hospital", result.project_name.lower())

    def test_detect_domain_hospital(self):
        result = self.processor.parse("build hospital management system")
        self.assertEqual(result.domain, "hospital")

    def test_detect_domain_ecommerce(self):
        result = self.processor.parse("build ecommerce platform")
        self.assertEqual(result.domain, "ecommerce")

    def test_detect_domain_general(self):
        result = self.processor.parse("build a todo app")
        self.assertEqual(result.domain, "general")

    def test_clean_text_removes_fillers(self):
        result = self.processor.parse("please build hospital management system")
        self.assertNotIn("please", result.cleaned_text)
        self.assertIn("build", result.cleaned_text)

    def test_confidence_scores(self):
        create_result = self.processor.parse("build hospital")
        chat_result = self.processor.parse("hello there")
        self.assertGreater(create_result.confidence, chat_result.confidence)

    def test_parsed_intent_to_dict(self):
        result = self.processor.parse("build hospital")
        data = result.to_dict()
        self.assertIn("intent", data)
        self.assertIn("project_name", data)
        self.assertIn("domain", data)
        self.assertIn("language", data.get("raw_entities", {}))

    def test_detect_language_english(self):
        result = self.processor.parse("build hospital management system")
        self.assertEqual(result.raw_entities.get("language"), "english")

    def test_detect_language_hindi(self):
        result = self.processor.parse("बनाओ hospital management system")
        self.assertEqual(result.raw_entities.get("language"), "hindi")

    def test_detect_language_hinglish(self):
        result = self.processor.parse("banao hospital management system")
        self.assertEqual(result.raw_entities.get("language"), "hinglish")

    def test_detect_language_mixed_hinglish(self):
        result = self.processor.parse("ek hospital management system banao")
        self.assertEqual(result.raw_entities.get("language"), "hinglish")


class TestHinglishResponseGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = HinglishResponseGenerator()

    def test_generate_welcome(self):
        response = self.generator.generate("welcome")
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)

    def test_generate_thinking(self):
        response = self.generator.generate("thinking")
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)

    def test_generate_engineering_started(self):
        response = self.generator.generate("engineering_started", project_name="Hospital")
        self.assertIn("Hospital", response)

    def test_generate_error(self):
        response = self.generator.generate("error", error="test error")
        self.assertIn("test error", response)

    def test_help_message(self):
        message = self.generator.help_message(language="hinglish")
        self.assertIn("JARVIS", message)
        self.assertIn("build", message.lower())
        self.assertIn("banao", message.lower())

    def test_generate_english_response(self):
        response = self.generator.generate("welcome", language="english")
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
        self.assertIn("Jarvis", response)

    def test_generate_hindi_response(self):
        response = self.generator.generate("welcome", language="hindi")
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
        # Should contain Devanagari script
        self.assertTrue(any('\u0900' <= c <= '\u097F' for c in response))

    def test_generate_hinglish_response(self):
        response = self.generator.generate("welcome", language="hinglish")
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
        # Hinglish should have either English or Hindi words
        self.assertTrue(
            any(word in response.lower() for word in ["namaste", "hello", "hey", "main", "aapke", "mujhe", "madad"]) or
            any('\u0900' <= c <= '\u097F' for c in response)
        )


if __name__ == "__main__":
    unittest.main()
