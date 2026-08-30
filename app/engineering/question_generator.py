"""Question generator for engineering workflow.

Generates clarifying questions when requirement analysis
detects missing or ambiguous information.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ClarifyingQuestion:
    """A single clarifying question."""

    id: str
    category: str
    question: str
    options: List[str] = field(default_factory=list)
    required: bool = True
    context: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "question": self.question,
            "options": list(self.options),
            "required": self.required,
            "context": self.context,
        }


@dataclass
class QuestionSet:
    """Collection of clarifying questions."""

    questions: List[ClarifyingQuestion] = field(default_factory=list)
    total: int = 0
    required: int = 0

    def to_dict(self) -> dict:
        return {
            "questions": [q.to_dict() for q in self.questions],
            "total": self.total,
            "required": self.required,
        }


class QuestionGenerator:
    """Generate clarifying questions for missing requirement information.

    Uses domain-specific templates to generate human-like questions
    that an engineer would ask during requirement gathering.
    """

    # Question templates by missing information category
    QUESTION_TEMPLATES = {
        "authentication": [
            "Should authentication use JWT tokens?",
            "Do you need OAuth / SSO integration?",
            "Should password reset be email-based?",
            "Do you need role-based access control (RBAC)?",
            "Should sessions expire after inactivity?",
        ],
        "deployment": [
            "Should I containerize with Docker?",
            "Do you need Kubernetes orchestration?",
            "Which cloud provider: AWS, Azure, or GCP?",
            "Do you need CI/CD pipeline?",
            "Should I set up auto-scaling?",
        ],
        "database": [
            "Should I use PostgreSQL or MySQL?",
            "Do you need database migrations (Alembic)?",
            "Should I add database connection pooling?",
            "Do you need read replicas for scaling?",
            "Should sensitive data be encrypted at rest?",
        ],
        "testing": [
            "What's the target test coverage percentage?",
            "Should I use pytest or unittest?",
            "Do you need integration tests?",
            "Should I include load testing?",
            "Do you need E2E tests with Playwright?",
        ],
        "security": [
            "Should I implement rate limiting?",
            "Do you need HTTPS / SSL enforcement?",
            "Should sensitive data be encrypted in transit?",
            "Do you need input validation and sanitization?",
            "Should I add security headers (CSP, HSTS)?",
        ],
        "scalability": [
            "Should I implement caching (Redis)?",
            "Do you need background job processing (Celery)?",
            "Should I add a message queue (RabbitMQ/Kafka)?",
            "Do you need CDN for static assets?",
            "Should I implement rate limiting and throttling?",
        ],
        "frontend": [
            "Should the frontend be React or Vue?",
            "Do you need a design system (Tailwind/MUI)?",
            "Should I implement client-side routing?",
            "Do you need form validation library?",
            "Should I add state management (Redux/Zustand)?",
        ],
        "api": [
            "Should API be REST or GraphQL?",
            "Do you need API versioning?",
            "Should I add request/response validation?",
            "Do you need API documentation (Swagger/OpenAPI)?",
            "Should I implement API rate limiting?",
        ],
        "storage": [
            "Should I use S3-compatible object storage?",
            "Do you need file upload functionality?",
            "Should I add CDN for media files?",
            "Do you need image processing/resizing?",
        ],
        "monitoring": [
            "Should I add application monitoring (Prometheus/Grafana)?",
            "Do you need distributed tracing (OpenTelemetry)?",
            "Should I implement structured logging?",
            "Do you need health check endpoints?",
            "Should I add error tracking (Sentry)?",
        ],
    }

    # Domain-specific extra questions
    DOMAIN_QUESTIONS = {
        "hospital": [
            "Do you need patient record encryption (HIPAA)?",
            "Should appointments support recurring visits?",
            "Do you need SMS/email reminders?",
            "Should billing integrate with insurance?",
            "Do you need lab report generation?",
        ],
        "ecommerce": [
            "Should I integrate payment gateway (Stripe/Razorpay)?",
            "Do you need inventory management?",
            "Should I add product search (Elasticsearch)?",
            "Do you need order tracking?",
            "Should I implement wishlist and reviews?",
        ],
        "education": [
            "Do you need online quiz/exam functionality?",
            "Should I add assignment submission?",
            "Do you need grade calculation automation?",
            "Should I implement attendance tracking?",
            "Do you need parent-teacher communication?",
        ],
        "finance": [
            "Should I implement transaction encryption?",
            "Do you need audit logging?",
            "Should I add fraud detection?",
            "Do you need multi-currency support?",
            "Should I implement compliance reporting?",
        ],
        "social": [
            "Should I implement real-time chat (WebSocket)?",
            "Do you need content moderation?",
            "Should I add push notifications?",
            "Do you need media upload/compression?",
            "Should I implement user blocking/reporting?",
        ],
    }

    def generate(self, analysis) -> QuestionSet:
        """Generate questions based on requirement analysis.

        Args:
            analysis: RequirementAnalysis from RequirementAnalyzer.

        Returns:
            QuestionSet with clarifying questions.
        """
        questions = []
        question_id = 1

        # Questions for missing information
        for missing in analysis.missing_information:
            templates = self.QUESTION_TEMPLATES.get(missing, [])
            if templates:
                selected = random.sample(templates, min(2, len(templates)))
                for q in selected:
                    questions.append(ClarifyingQuestion(
                        id=f"q{question_id:03d}",
                        category=missing,
                        question=q,
                        options=self._get_options(missing),
                        required=True,
                        context=f"Required for {missing} setup",
                    ))
                    question_id += 1

        # Domain-specific questions
        domain_questions = self.DOMAIN_QUESTIONS.get(analysis.domain, [])
        for q in random.sample(domain_questions, min(3, len(domain_questions))):
            questions.append(ClarifyingQuestion(
                id=f"q{question_id:03d}",
                category="domain_specific",
                question=q,
                options=["Yes", "No", "Later"],
                required=False,
                context=f"Specific to {analysis.domain} domain",
            ))
            question_id += 1

        required_count = sum(1 for q in questions if q.required)
        return QuestionSet(
            questions=questions,
            total=len(questions),
            required=required_count,
        )

    def _get_options(self, category: str) -> List[str]:
        """Get common options for a question category."""
        options_map = {
            "authentication": ["JWT", "OAuth2", "Session-based", "SSO"],
            "database": ["PostgreSQL", "MySQL", "MongoDB", "SQLite"],
            "deployment": ["Docker", "Kubernetes", "AWS", "Azure", "GCP", "VPS"],
            "frontend": ["React", "Vue", "Angular", "Svelte", "Next.js"],
            "testing": ["pytest", "unittest", "Jest", "Mocha"],
        }
        return options_map.get(category, ["Yes", "No", "Default", "Custom"])
