"""Tests for question_generator.py."""

import pytest

from app.engineering.question_generator import QuestionGenerator, QuestionSet


class TestQuestionGenerator:
    def setup_method(self):
        self.generator = QuestionGenerator()

    def test_generate_questions(self):
        analysis = type('obj', (object,), {
            'missing_information': ['authentication', 'deployment', 'testing'],
            'domain': 'hospital',
        })()
        questions = self.generator.generate(analysis)
        assert isinstance(questions, QuestionSet)
        assert questions.total > 0

    def test_required_questions_count(self):
        analysis = type('obj', (object,), {
            'missing_information': ['authentication', 'database'],
            'domain': 'ecommerce',
        })()
        questions = self.generator.generate(analysis)
        assert questions.required > 0

    def test_question_structure(self):
        analysis = type('obj', (object,), {
            'missing_information': ['security'],
            'domain': 'default',
        })()
        questions = self.generator.generate(analysis)
        assert len(questions.questions) > 0
        q = questions.questions[0]
        assert hasattr(q, 'id')
        assert hasattr(q, 'category')
        assert hasattr(q, 'question')
        assert hasattr(q, 'options')

    def test_to_dict(self):
        analysis = type('obj', (object,), {
            'missing_information': ['authentication'],
            'domain': 'education',
        })()
        questions = self.generator.generate(analysis)
        data = questions.to_dict()
        assert 'questions' in data
        assert 'total' in data
        assert 'required' in data

    def test_domain_specific_questions(self):
        analysis = type('obj', (object,), {
            'missing_information': [],
            'domain': 'hospital',
        })()
        questions = self.generator.generate(analysis)
        # Should still generate domain-specific questions
        assert questions.total > 0
