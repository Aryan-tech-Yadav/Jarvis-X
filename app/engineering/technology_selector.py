"""Technology selector for engineering workflow.

Automatically selects appropriate technologies based on:
  - project requirements
  - domain
  - scale
  - team expertise
  - existing patterns

Output:
  - backend framework
  - frontend framework
  - database
  - cache
  - queue
  - deployment platform
  - testing framework
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TechnologyStack:
    """Selected technology stack for a project."""

    backend: str = "FastAPI"
    frontend: str = "React"
    database: str = "PostgreSQL"
    cache: str = "Redis"
    queue: str = "Celery"
    storage: str = "S3"
    monitoring: str = "Prometheus"
    testing: str = "pytest"
    deployment: str = "Docker"
    ci_cd: str = "GitHub Actions"
    reasoning: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "backend": self.backend,
            "frontend": self.frontend,
            "database": self.database,
            "cache": self.cache,
            "queue": self.queue,
            "storage": self.storage,
            "monitoring": self.monitoring,
            "testing": self.testing,
            "deployment": self.deployment,
            "ci_cd": self.ci_cd,
            "reasoning": dict(self.reasoning),
        }


class TechnologySelector:
    """Select technologies based on project requirements.

    Uses rule-based selection with domain-specific preferences.
    """

    # Domain-specific technology preferences
    DOMAIN_PREFERENCES = {
        "hospital": {
            "backend": "FastAPI",
            "frontend": "React",
            "database": "PostgreSQL",
            "cache": "Redis",
            "testing": "pytest",
            "deployment": "Docker",
        },
        "ecommerce": {
            "backend": "Django",
            "frontend": "React",
            "database": "PostgreSQL",
            "cache": "Redis",
            "queue": "Celery",
            "testing": "pytest",
            "deployment": "Docker",
        },
        "finance": {
            "backend": "FastAPI",
            "frontend": "React",
            "database": "PostgreSQL",
            "cache": "Redis",
            "queue": "Kafka",
            "monitoring": "Prometheus",
            "testing": "pytest",
        },
        "social": {
            "backend": "FastAPI",
            "frontend": "React Native",
            "database": "PostgreSQL",
            "cache": "Redis",
            "queue": "Celery",
            "storage": "S3",
            "testing": "pytest",
        },
        "education": {
            "backend": "Django",
            "frontend": "React",
            "database": "PostgreSQL",
            "cache": "Redis",
            "testing": "pytest",
            "deployment": "Docker",
        },
        "iot": {
            "backend": "FastAPI",
            "frontend": "React",
            "database": "TimescaleDB",
            "queue": "MQTT",
            "monitoring": "Prometheus",
            "testing": "pytest",
        },
    }

    # Scale-based overrides
    SCALE_OVERRIDES = {
        "enterprise": {
            "backend": "FastAPI",
            "database": "PostgreSQL",
            "queue": "Kafka",
            "monitoring": "Prometheus",
            "deployment": "Kubernetes",
        },
        "startup": {
            "backend": "FastAPI",
            "database": "PostgreSQL",
            "deployment": "Docker",
            "ci_cd": "GitHub Actions",
        },
    }

    def select(self, requirement_analysis: Dict) -> TechnologyStack:
        """Select technology stack based on requirement analysis."""
        domain = requirement_analysis.get("domain", "general")
        project_type = requirement_analysis.get("project_type", "web")
        scale = requirement_analysis.get("scale", "startup")
        features = requirement_analysis.get("features", [])

        # Get domain preferences
        prefs = self.DOMAIN_PREFERENCES.get(domain, {})

        # Apply scale overrides
        scale_overrides = self.SCALE_OVERRIDES.get(scale, {})

        # Build reasoning
        reasoning = {}

        # Backend selection
        backend = scale_overrides.get("backend", prefs.get("backend", "FastAPI"))
        reasoning["backend"] = f"Selected {backend} for {domain} domain - {'high performance async' if backend == 'FastAPI' else 'rapid development with admin panel'}"

        # Frontend selection
        frontend = prefs.get("frontend", "React")
        if project_type == "mobile":
            frontend = "React Native"
        reasoning["frontend"] = f"Selected {frontend} - {'mobile-first' if project_type == 'mobile' else 'component-based SPA'}"

        # Database selection
        database = scale_overrides.get("database", prefs.get("database", "PostgreSQL"))
        if "real-time" in features or "analytics" in features:
            database = "TimescaleDB" if "iot" in domain else "PostgreSQL"
        reasoning["database"] = f"Selected {database} - {'time-series optimized' if 'TimescaleDB' in database else 'reliable relational DB'}"

        # Cache selection
        cache = prefs.get("cache", "Redis")
        reasoning["cache"] = f"Selected {cache} for session management and caching"

        # Queue selection
        queue = prefs.get("queue", "Celery")
        reasoning["queue"] = f"Selected {queue} for async task processing"

        # Testing selection
        testing = prefs.get("testing", "pytest")
        reasoning["testing"] = f"Selected {testing} - Python-native testing framework"

        # Deployment selection
        deployment = scale_overrides.get("deployment", prefs.get("deployment", "Docker"))
        reasoning["deployment"] = f"Selected {deployment} for containerized deployment"

        return TechnologyStack(
            backend=backend,
            frontend=frontend,
            database=database,
            cache=cache,
            queue=queue,
            storage=scale_overrides.get("storage", prefs.get("storage", "S3")),
            monitoring=scale_overrides.get("monitoring", prefs.get("monitoring", "Prometheus")),
            testing=testing,
            deployment=deployment,
            ci_cd=scale_overrides.get("ci_cd", prefs.get("ci_cd", "GitHub Actions")),
            reasoning=reasoning,
        )

    def get_alternatives(self, category: str, primary: str) -> List[str]:
        """Get alternative technologies for a category."""
        alternatives = {
            "backend": ["FastAPI", "Django", "Flask", "Express.js", "Spring Boot"],
            "frontend": ["React", "Vue.js", "Angular", "Svelte", "Next.js"],
            "database": ["PostgreSQL", "MySQL", "MongoDB", "SQLite", "TimescaleDB"],
            "cache": ["Redis", "Memcached", "In-Memory"],
            "queue": ["Celery", "Kafka", "RabbitMQ", "AWS SQS"],
            "testing": ["pytest", "unittest", "Jest", "Mocha"],
            "deployment": ["Docker", "Kubernetes", "AWS ECS", "Heroku"],
        }
        return [alt for alt in alternatives.get(category, []) if alt != primary]
