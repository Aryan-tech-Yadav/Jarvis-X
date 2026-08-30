"""Project type detection and tech-stack selection.

Detects project type from user prompt and returns the optimal
tech stack and template configuration.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ProjectType(str, Enum):
    GAME = "game"
    WEB_APP = "web_app"
    API = "api"
    CLI = "cli"
    LIBRARY = "library"
    MOBILE = "mobile"
    DATA_SCIENCE = "data_science"
    AUTOMATION = "automation"
    UNKNOWN = "unknown"


@dataclass
class TechStack:
    """Technology stack for a project."""
    project_type: str
    backend: str = ""
    frontend: str = ""
    database: str = ""
    runtime: str = "python"
    frameworks: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    template_id: str = "default"
    rationale: str = ""


@dataclass
class ProjectDetection:
    """Result of project type detection."""
    project_type: ProjectType
    tech_stack: TechStack
    confidence: float
    matched_keywords: List[str] = field(default_factory=list)
    template_path: str = ""
    description: str = ""


class ProjectTypeDetector:
    """Detect project type and select optimal tech stack.

    Uses keyword matching + LLM reasoning for accurate detection.
    """

    DETECTION_RULES: List[Tuple[ProjectType, List[str], TechStack]] = [
        (
            ProjectType.GAME,
            ["tic tac toe", "snake game", "pong", "flappy bird", "game", "chess", "puzzle"],
            TechStack(
                project_type="game",
                runtime="python",
                backend="",
                frontend="",
                database="",
                frameworks=["pygame"],
                tools=["pytest"],
                template_id="pygame_game",
                rationale="Simple 2D games work best with Pygame - no overkill web stack needed",
            ),
        ),
        (
            ProjectType.GAME,
            ["web game", "browser game", "html game", "javascript game"],
            TechStack(
                project_type="game",
                runtime="javascript",
                backend="",
                frontend="html5",
                database="",
                frameworks=["html5", "css3", "javascript"],
                tools=["jest"],
                template_id="web_game",
                rationale="Browser-based games use vanilla JS/HTML5 Canvas",
            ),
        ),
        (
            ProjectType.WEB_APP,
            ["portfolio", "personal website", "blog", "landing page", "static site"],
            TechStack(
                project_type="web_app",
                runtime="javascript",
                backend="",
                frontend="react",
                database="",
                frameworks=["react", "vite"],
                tools=["vite"],
                template_id="react_portfolio",
                rationale="Portfolio sites are static and React provides clean component structure",
            ),
        ),
        (
            ProjectType.WEB_APP,
            ["ecommerce", "e-commerce", "online store", "shop", "marketplace", "shopping cart"],
            TechStack(
                project_type="web_app",
                runtime="javascript",
                backend="next.js",
                frontend="react",
                database="postgresql",
                frameworks=["next.js", "react", "tailwindcss"],
                tools=["prisma", "stripe"],
                template_id="nextjs_ecommerce",
                rationale="E-commerce needs SSR, routing, and database - Next.js is the standard",
            ),
        ),
        (
            ProjectType.API,
            ["rest api", "api", "backend", "microservice", "fastapi", "flask api", "node api"],
            TechStack(
                project_type="api",
                runtime="python",
                backend="fastapi",
                frontend="",
                database="postgresql",
                frameworks=["fastapi", "sqlalchemy", "pydantic"],
                tools=["pytest", "uvicorn"],
                template_id="fastapi_api",
                rationale="FastAPI provides auto-docs, validation, and async support out of the box",
            ),
        ),
        (
            ProjectType.API,
            ["node api", "express api", "javascript backend", "typescript api"],
            TechStack(
                project_type="api",
                runtime="javascript",
                backend="express",
                frontend="",
                database="mongodb",
                frameworks=["express", "mongoose"],
                tools=["jest", "nodemon"],
                template_id="express_api",
                rationale="Express is the standard lightweight Node.js backend framework",
            ),
        ),
        (
            ProjectType.CLI,
            ["cli", "command line", "terminal app", "tool", "utility"],
            TechStack(
                project_type="cli",
                runtime="python",
                backend="",
                frontend="",
                database="",
                frameworks=["click", "rich"],
                tools=["pytest"],
                template_id="python_cli",
                rationale="CLI tools should be lightweight - Click + Rich provides clean UX",
            ),
        ),
        (
            ProjectType.MOBILE,
            ["mobile app", "android", "ios", "react native", "flutter"],
            TechStack(
                project_type="mobile",
                runtime="javascript",
                backend="",
                frontend="react native",
                database="sqlite",
                frameworks=["react native", "expo"],
                tools=["expo"],
                template_id="react_native_app",
                rationale="React Native allows cross-platform mobile development",
            ),
        ),
        (
            ProjectType.DATA_SCIENCE,
            ["data science", "machine learning", "ml", "ai model", "prediction", "analysis"],
            TechStack(
                project_type="data_science",
                runtime="python",
                backend="",
                frontend="",
                database="",
                frameworks=["pandas", "numpy", "scikit-learn", "matplotlib"],
                tools=["jupyter", "pytest"],
                template_id="data_science",
                rationale="Data science projects need pandas, numpy, and visualization libraries",
            ),
        ),
        (
            ProjectType.AUTOMATION,
            ["automation", "bot", "scraper", "crawler", "scheduler", "etl"],
            TechStack(
                project_type="automation",
                runtime="python",
                backend="",
                frontend="",
                database="",
                frameworks=["selenium", "schedule", "requests"],
                tools=["pytest", "docker"],
                template_id="python_automation",
                rationale="Automation scripts need robust HTTP, scheduling, and browser control",
            ),
        ),
        (
            ProjectType.WEB_APP,
            ["chat app", "chatbot", "messaging", "real-time", "websocket"],
            TechStack(
                project_type="web_app",
                runtime="python",
                backend="fastapi",
                frontend="react",
                database="postgresql",
                frameworks=["fastapi", "websockets", "react"],
                tools=["pytest", "docker"],
                template_id="fastapi_react_chat",
                rationale="Chat apps need WebSocket backend + reactive frontend",
            ),
        ),
    ]

    def detect(self, prompt: str, use_llm: bool = True) -> ProjectDetection:
        """Detect project type from user prompt.

        Args:
            prompt: User's natural language request
            use_llm: Whether to use LLM for ambiguous cases

        Returns:
            ProjectDetection with type, tech stack, and confidence
        """
        prompt_lower = prompt.lower()

        # Rule-based detection first
        for project_type, keywords, tech_stack in self.DETECTION_RULES:
            matched = [
                kw for kw in keywords
                if re.search(r"\b" + re.escape(kw) + r"\b", prompt_lower)
            ]
            if matched:
                confidence = min(0.95, 0.7 + 0.05 * len(matched))
                return ProjectDetection(
                    project_type=project_type,
                    tech_stack=tech_stack,
                    confidence=confidence,
                    matched_keywords=matched,
                    template_path=self._get_template_path(tech_stack.template_id),
                    description=f"Detected {project_type.value} project with {tech_stack.rationale}",
                )

        # LLM-based detection for ambiguous cases
        if use_llm:
            return self._llm_detect(prompt)

        return ProjectDetection(
            project_type=ProjectType.UNKNOWN,
            tech_stack=TechStack(
                project_type="unknown",
                runtime="python",
                template_id="default",
                rationale="No specific pattern matched - using safe default",
            ),
            confidence=0.3,
            description="Could not determine project type - using default Python template",
        )

    def _llm_detect(self, prompt: str) -> ProjectDetection:
        """Use LLM to detect project type for ambiguous inputs."""
        try:
            from app.ai.ai_manager import AIManager
            ai = AIManager()

            llm_prompt = f"""Analyze this project request and classify it into exactly one type:
- game (2D games, puzzles, arcade)
- web_app (websites, portfolios, e-commerce, dashboards)
- api (REST APIs, backend services, microservices)
- cli (command line tools, utilities)
- library (reusable packages, SDKs)
- mobile (iOS/Android apps)
- data_science (ML, analysis, predictions)
- automation (bots, scrapers, schedulers)

Request: {prompt}

Return JSON only:
{{"type": "game", "confidence": 0.95, "reason": "User wants a tic tac toe game"}}"""

            response = ai.ask(llm_prompt)
            import json
            import re

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                ptype = data.get("type", "unknown")
                try:
                    project_type = ProjectType(ptype)
                except ValueError:
                    project_type = ProjectType.UNKNOWN

                tech_stack = self._get_default_stack(project_type)
                return ProjectDetection(
                    project_type=project_type,
                    tech_stack=tech_stack,
                    confidence=float(data.get("confidence", 0.5)),
                    matched_keywords=[],
                    template_path=self._get_template_path(tech_stack.template_id),
                    description=data.get("reason", "LLM-based detection"),
                )
        except Exception:
            pass

        return ProjectDetection(
            project_type=ProjectType.UNKNOWN,
            tech_stack=self._get_default_stack(ProjectType.UNKNOWN),
            confidence=0.3,
            description="LLM detection failed - using default",
        )

    def _get_default_stack(self, project_type: ProjectType) -> TechStack:
        """Get default tech stack for a project type."""
        defaults = {
            ProjectType.GAME: TechStack("game", runtime="python", frameworks=["pygame"], template_id="pygame_game", rationale="Default game stack"),
            ProjectType.WEB_APP: TechStack("web_app", runtime="python", backend="fastapi", frontend="react", database="postgresql", frameworks=["fastapi", "react"], template_id="fastapi_react", rationale="Full-stack web app"),
            ProjectType.API: TechStack("api", runtime="python", backend="fastapi", database="postgresql", frameworks=["fastapi", "sqlalchemy"], template_id="fastapi_api", rationale="Production-ready API"),
            ProjectType.CLI: TechStack("cli", runtime="python", frameworks=["click", "rich"], template_id="python_cli", rationale="CLI tool"),
            ProjectType.LIBRARY: TechStack("library", runtime="python", frameworks=["pytest"], template_id="python_library", rationale="Python library"),
            ProjectType.MOBILE: TechStack("mobile", runtime="javascript", frontend="react native", frameworks=["react native", "expo"], template_id="react_native_app", rationale="Mobile app"),
            ProjectType.DATA_SCIENCE: TechStack("data_science", runtime="python", frameworks=["pandas", "numpy", "matplotlib"], template_id="data_science", rationale="Data science project"),
            ProjectType.AUTOMATION: TechStack("automation", runtime="python", frameworks=["requests", "schedule"], template_id="python_automation", rationale="Automation script"),
            ProjectType.UNKNOWN: TechStack("unknown", runtime="python", frameworks=[""], template_id="default", rationale="Safe default Python"),
        }
        return defaults.get(project_type, defaults[ProjectType.UNKNOWN])

    def _get_template_path(self, template_id: str) -> str:
        """Get filesystem path for a template."""
        return f"templates/{template_id}"

    def get_tech_stack(self, prompt: str) -> TechStack:
        """Convenience method to get just the tech stack."""
        detection = self.detect(prompt)
        return detection.tech_stack
