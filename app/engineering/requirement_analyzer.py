"""Requirement analyzer for engineering workflow.

Analyzes natural language requirements and extracts structured
engineering information:
  - domain, project type, tech stack
  - roles, modules
  - missing information / ambiguities
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RequirementAnalysis:
    """Structured analysis of a project requirement."""

    raw_requirement: str
    project_name: str = ""
    domain: str = "general"
    project_type: str = "web"
    backend: Optional[str] = None
    frontend: Optional[str] = None
    database: Optional[str] = None
    cache: Optional[str] = None
    queue: Optional[str] = None
    storage: Optional[str] = None
    monitoring: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    modules: List[str] = field(default_factory=list)
    missing_information: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "raw_requirement": self.raw_requirement,
            "project_name": self.project_name,
            "domain": self.domain,
            "project_type": self.project_type,
            "backend": self.backend,
            "frontend": self.frontend,
            "database": self.database,
            "cache": self.cache,
            "queue": self.queue,
            "storage": self.storage,
            "monitoring": self.monitoring,
            "roles": list(self.roles),
            "modules": list(self.modules),
            "missing_information": list(self.missing_information),
            "keywords": list(self.keywords),
            "confidence": round(self.confidence, 2),
        }


class RequirementAnalyzer:
    """Analyze project requirements using NLP heuristics.

    Detects domain, project type, tech stack, roles, and modules
    from natural language descriptions.
    """

    # Domain keywords
    DOMAIN_KEYWORDS = {
        "hospital": ["hospital", "clinic", "patient", "doctor", "medical", "healthcare", "appointment", "pharmacy"],
        "ecommerce": ["ecommerce", "shop", "store", "cart", "checkout", "product", "payment", "order"],
        "education": ["education", "school", "student", "course", "learning", "exam", "teacher", "classroom"],
        "finance": ["finance", "bank", "transaction", "payment", "loan", "account", "billing", "invoice"],
        "social": ["social", "chat", "message", "post", "feed", "friend", "follow", "community"],
        "iot": ["iot", "sensor", "device", "embedded", "raspberry", "arduino", "hardware"],
        "ai": ["ai", "ml", "machine learning", "deep learning", "neural", "model", "training", "dataset"],
        "blockchain": ["blockchain", "crypto", "nft", "smart contract", "web3", "ethereum", "bitcoin"],
    }

    # Project type keywords
    PROJECT_TYPE_KEYWORDS = {
        "game": ["game", "tic tac toe", "snake", "pong", "chess", "puzzle", "arcade"],
        "web": ["web", "website", "web app", "dashboard", "portal", "saas", "spa"],
        "mobile": ["mobile", "android", "ios", "app", "flutter", "react native", "pwa"],
        "api": ["api", "rest", "graphql", "microservice", "backend", "service"],
        "desktop": ["desktop", "gui", "tkinter", "electron", "qt", "pyqt"],
        "cli": ["cli", "command line", "terminal", "tool"],
        "library": ["library", "sdk", "package", "module"],
    }

    # Tech stack defaults by project type
    TECH_STACK_DEFAULTS = {
        "game": {"backend": "Python", "frontend": "Pygame", "database": "None"},
        "web": {"backend": "FastAPI", "frontend": "React", "database": "PostgreSQL", "cache": "Redis", "monitoring": "Prometheus"},
        "api": {"backend": "FastAPI", "database": "PostgreSQL", "cache": "Redis", "queue": "Celery", "monitoring": "Prometheus"},
        "mobile": {"backend": "FastAPI", "frontend": "Flutter", "database": "PostgreSQL", "storage": "S3"},
        "desktop": {"backend": "Python", "frontend": "Tkinter", "database": "SQLite"},
        "cli": {"backend": "Python", "database": "SQLite"},
        "library": {"backend": "Python", "database": "None"},
    }

    # Common roles by domain
    ROLE_PATTERNS = {
        "hospital": ["Admin", "Doctor", "Patient", "Nurse", "Receptionist"],
        "ecommerce": ["Admin", "Customer", "Seller", "Delivery", "Support"],
        "education": ["Admin", "Teacher", "Student", "Parent", "Staff"],
        "finance": ["Admin", "Accountant", "Customer", "Auditor", "Manager"],
        "social": ["Admin", "User", "Moderator", "Creator"],
        "default": ["Admin", "User"],
    }

    # Common modules by domain
    MODULE_PATTERNS = {
        "hospital": ["Appointments", "Billing", "Reports", "Pharmacy", "Lab", "Wards", "Staff"],
        "ecommerce": ["Products", "Cart", "Checkout", "Orders", "Inventory", "Reviews", "Analytics"],
        "education": ["Courses", "Exams", "Attendance", "Grades", "Library", "Fees", "Events"],
        "finance": ["Accounts", "Transactions", "Loans", "Cards", "Statements", "Compliance", "Audit"],
        "social": ["Posts", "Messages", "Notifications", "Search", "Feed", "Stories", "Groups"],
        "default": ["Authentication", "Dashboard", "Settings", "Reports", "API"],
    }

    # Missing info triggers
    MISSING_INFO_TRIGGERS = {
        "authentication": ["auth", "login", "jwt", "oauth", "sso", "password"],
        "deployment": ["deploy", "docker", "kubernetes", "k8s", "aws", "azure", "gcp", "cloud", "ci/cd"],
        "database": ["database", "db", "sql", "nosql", "postgres", "mysql", "mongodb"],
        "testing": ["test", "pytest", "jest", "coverage"],
        "security": ["security", "encryption", "https", "ssl", "rate limit"],
        "scalability": ["scale", "performance", "load balancer", "cdn"],
    }

    def analyze(self, requirement: str) -> RequirementAnalysis:
        """Analyze a project requirement string.

        Args:
            requirement: Natural language project description.

        Returns:
            RequirementAnalysis with extracted information.
        """
        text = requirement.strip()
        lower = text.lower()
        words = re.findall(r"\b\w+\b", lower)

        # Simple project name extraction
        project_name = text
        for prefix in ["build", "create", "make", "design", "develop", "implement", "a", "an"]:
            if lower.startswith(prefix + " "):
                project_name = text[len(prefix):].strip()
                break
        project_name = project_name.strip(" :.-")
        if not project_name:
            project_name = text[:50]

        analysis = RequirementAnalysis(raw_requirement=requirement, project_name=project_name)

        # Domain detection
        self._detect_domain(lower, words, analysis)

        # Project type detection
        self._detect_project_type(lower, words, analysis)

        # Tech stack
        self._infer_tech_stack(analysis)

        # Roles
        self._detect_roles(analysis)

        # Modules
        self._detect_modules(analysis)

        # Keywords
        analysis.keywords = list(set(words))

        # Missing information
        self._detect_missing_info(lower, analysis)

        # Confidence
        analysis.confidence = self._compute_confidence(analysis)

        return analysis

    def _detect_domain(self, text: str, words: List[str], analysis: RequirementAnalysis):
        """Detect project domain."""
        scores = {}
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            scores[domain] = score

        best_domain = max(scores, key=scores.get) if scores else "general"
        if scores.get(best_domain, 0) > 0:
            analysis.domain = best_domain

    def _detect_project_type(self, text: str, words: List[str], analysis: RequirementAnalysis):
        """Detect project type."""
        scores = {}
        for ptype, keywords in self.PROJECT_TYPE_KEYWORDS.items():
            score = sum(
                1 for kw in keywords
                if re.search(r"\b" + re.escape(kw) + r"\b", text)
            )
            scores[ptype] = score

        best_type = max(scores, key=scores.get) if scores and max(scores.values()) > 0 else "web"
        
        # If domain is detected, prefer web/API for non-mobile domains
        if analysis.domain != "general" and best_type == "mobile":
            # Only use mobile if explicitly mentioned
            mobile_keywords = ["mobile app", "android", "ios", "flutter", "react native", "pwa"]
            if not any(kw in text for kw in mobile_keywords):
                best_type = "web"
        
        analysis.project_type = best_type

    def _infer_tech_stack(self, analysis: RequirementAnalysis):
        """Infer default tech stack based on project type."""
        defaults = self.TECH_STACK_DEFAULTS.get(analysis.project_type, {})
        analysis.backend = defaults.get("backend")
        analysis.frontend = defaults.get("frontend")
        analysis.database = defaults.get("database")
        analysis.cache = defaults.get("cache")
        analysis.queue = defaults.get("queue")
        analysis.storage = defaults.get("storage")
        analysis.monitoring = defaults.get("monitoring")

        # Override based on domain keywords
        if "mobile" in analysis.raw_requirement.lower() or "app" in analysis.raw_requirement.lower():
            if "android" in analysis.raw_requirement.lower() or "ios" in analysis.raw_requirement.lower():
                analysis.frontend = "Flutter"
                analysis.project_type = "mobile"

        if "api" in analysis.raw_requirement.lower() and "rest" in analysis.raw_requirement.lower():
            analysis.project_type = "api"
            analysis.frontend = None

    def _detect_roles(self, analysis: RequirementAnalysis):
        """Detect user roles."""
        roles = self.ROLE_PATTERNS.get(analysis.domain, self.ROLE_PATTERNS["default"])
        analysis.roles = list(roles)

    def _detect_modules(self, analysis: RequirementAnalysis):
        """Detect project modules."""
        modules = self.MODULE_PATTERNS.get(analysis.domain, self.MODULE_PATTERNS["default"])
        analysis.modules = list(modules)

    def _detect_missing_info(self, text: str, analysis: RequirementAnalysis):
        """Detect missing information that needs clarification."""
        for info_type, triggers in self.MISSING_INFO_TRIGGERS.items():
            if not any(trigger in text for trigger in triggers):
                analysis.missing_information.append(info_type)

    def _compute_confidence(self, analysis: RequirementAnalysis) -> float:
        """Compute confidence score 0.0-1.0."""
        score = 0.0
        if analysis.domain != "general":
            score += 0.3
        if analysis.backend:
            score += 0.2
        if analysis.database:
            score += 0.2
        if analysis.roles:
            score += 0.15
        if analysis.modules:
            score += 0.15
        return min(1.0, score)
