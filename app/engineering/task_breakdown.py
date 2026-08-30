"""Task breakdown for engineering workflow.

Breaks down system architecture into concrete, executable tasks
with priorities, estimates, and deliverables.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class EngineeringTask:
    """A single engineering task."""

    id: str
    title: str
    description: str
    priority: str = "medium"  # high, medium, low
    status: str = "pending"  # pending, in_progress, completed, failed
    estimated_hours: float = 1.0
    dependencies: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    category: str = "backend"
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "estimated_hours": self.estimated_hours,
            "dependencies": list(self.dependencies),
            "deliverables": list(self.deliverables),
            "category": self.category,
            "tags": list(self.tags),
        }


@dataclass
class TaskBreakdown:
    """Complete task breakdown for a project."""

    project_name: str
    tasks: List[EngineeringTask] = field(default_factory=list)
    total_tasks: int = 0
    total_estimated_hours: float = 0.0
    categories: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project_name": self.project_name,
            "tasks": [t.to_dict() for t in self.tasks],
            "total_tasks": self.total_tasks,
            "total_estimated_hours": round(self.total_estimated_hours, 1),
            "categories": list(self.categories),
        }


class TaskBreakdownEngine:
    """Break down architecture into executable engineering tasks.

    Creates granular tasks with priorities, estimates, and
    deliverable definitions.
    """

    # Task templates by category
    TASK_TEMPLATES = {
        "setup": [
            ("Initialize Project Structure", "Create project directory, setup git, initialize package", 1.0, ["Project folder", "Git repo", "requirements.txt"]),
            ("Setup Development Environment", "Configure dev tools, linters, formatters, IDE settings", 1.5, ["Dev config", "Linter setup"]),
            ("Configure CI/CD Pipeline", "Setup GitHub Actions / GitLab CI for testing and deployment", 2.0, ["CI config", "Test pipeline"]),
        ],
        "backend": [
            ("Create FastAPI Application", "Initialize FastAPI app with routers, middleware, config", 2.0, ["main.py", "routers/", "config.py"]),
            ("Design Database Schema", "Create SQLAlchemy models, migrations, relationships", 3.0, ["models.py", "migrations/", "schema.sql"]),
            ("Implement Authentication", "JWT auth, login/register endpoints, password hashing", 4.0, ["auth.py", "dependencies.py", "schemas.py"]),
            ("Implement CRUD Operations", "Create, read, update, delete for all entities", 6.0, ["CRUD modules", "API endpoints"]),
            ("Add Input Validation", "Pydantic schemas, request validation, error handling", 3.0, ["schemas.py", "validators.py"]),
            ("Implement Authorization", "Role-based access control, permission decorators", 4.0, ["RBAC system", "Permission checks"]),
            ("Add API Documentation", "Swagger/OpenAPI docs, example requests, descriptions", 2.0, ["OpenAPI specs", "Doc examples"]),
        ],
        "frontend": [
            ("Setup React Application", "Create React app, routing, state management, config", 2.0, ["src/", "package.json", "routes/"]),
            ("Create Authentication Pages", "Login, register, forgot password, protected routes", 4.0, ["Login.jsx", "Register.jsx", "AuthContext"]),
            ("Build Dashboard Layout", "Sidebar, header, navigation, responsive layout", 3.0, ["Layout.jsx", "Sidebar.jsx"]),
            ("Implement State Management", "Redux/Zustand store, actions, reducers, selectors", 3.0, ["store/", "actions/", "reducers/"]),
            ("Add Form Handling", "Form validation, error messages, submission logic", 3.0, ["Form components", "Validation utils"]),
        ],
        "testing": [
            ("Write Unit Tests", "Test business logic, models, utilities", 4.0, ["test_*.py", "Coverage report"]),
            ("Write Integration Tests", "Test API endpoints, database operations", 4.0, ["test_api.py", "Fixtures"]),
            ("Write E2E Tests", "End-to-end user flow testing", 3.0, ["E2E tests", "Test data"]),
            ("Setup Test Coverage", "Configure pytest, coverage reporting, thresholds", 1.5, ["pytest.ini", "Coverage config"]),
        ],
        "deployment": [
            ("Dockerize Application", "Create Dockerfile, docker-compose, multi-stage builds", 2.0, ["Dockerfile", "docker-compose.yml"]),
            ("Setup Production Config", "Environment variables, secrets, logging, monitoring", 2.5, ["Production config", "Env files"]),
            ("Database Migration Setup", "Alembic setup, migration scripts, rollback procedures", 2.0, ["alembic/", "Migration scripts"]),
            ("Deploy to Cloud", "Deploy to AWS/Azure/GCP, configure domain, SSL", 3.0, ["Deployment scripts", "Terraform/Pulumi"]),
        ],
        "documentation": [
            ("Write README", "Project overview, setup instructions, API docs", 2.0, ["README.md"]),
            ("Write Architecture Docs", "System design, data flow, component diagram", 2.0, ["ARCHITECTURE.md"]),
            ("Write API Documentation", "Endpoint docs, request/response examples", 2.0, ["API.md"]),
            ("Write Deployment Guide", "Deployment steps, environment setup, troubleshooting", 1.5, ["DEPLOYMENT.md"]),
        ],
    }

    # Priority weights
    PRIORITY_MAP = {
        "setup": "high",
        "backend": "high",
        "testing": "high",
        "deployment": "medium",
        "frontend": "medium",
        "documentation": "low",
    }

    def breakdown(self, architecture, analysis) -> TaskBreakdown:
        """Break down architecture into tasks.

        Args:
            architecture: SystemArchitecture from designer.
            analysis: RequirementAnalysis from analyzer.

        Returns:
            TaskBreakdown with all tasks.
        """
        tasks = []
        task_id = 1

        # Generate tasks based on project type and architecture
        categories = self._select_categories(analysis.project_type)
        
        for category in categories:
            templates = self.TASK_TEMPLATES.get(category, [])
            for title, description, hours, deliverables in templates:
                task = EngineeringTask(
                    id=f"TASK-{task_id:03d}",
                    title=title,
                    description=description,
                    priority=self.PRIORITY_MAP.get(category, "medium"),
                    estimated_hours=hours + random.uniform(-0.2, 0.2),
                    deliverables=deliverables,
                    category=category,
                    tags=[analysis.domain, analysis.project_type],
                )
                tasks.append(task)
                task_id += 1

        # Add domain-specific tasks
        domain_tasks = self._get_domain_tasks(analysis.domain)
        for title, description, hours, deliverables in domain_tasks:
            task = EngineeringTask(
                id=f"TASK-{task_id:03d}",
                title=title,
                description=description,
                priority="high",
                estimated_hours=hours,
                deliverables=deliverables,
                category="domain_specific",
                tags=[analysis.domain],
            )
            tasks.append(task)
            task_id += 1

        # Set dependencies
        tasks = self._set_dependencies(tasks)

        breakdown = TaskBreakdown(
            project_name=analysis.raw_requirement[:50],
            tasks=tasks,
            total_tasks=len(tasks),
            total_estimated_hours=sum(t.estimated_hours for t in tasks),
            categories=list(set(t.category for t in tasks)),
        )
        return breakdown

    def _select_categories(self, project_type: str) -> List[str]:
        """Select task categories based on project type."""
        if project_type == "web":
            return ["setup", "backend", "frontend", "testing", "deployment", "documentation"]
        elif project_type == "api":
            return ["setup", "backend", "testing", "deployment", "documentation"]
        elif project_type == "mobile":
            return ["setup", "backend", "frontend", "testing", "deployment", "documentation"]
        elif project_type == "cli":
            return ["setup", "backend", "testing", "documentation"]
        elif project_type == "desktop":
            return ["setup", "backend", "testing", "documentation"]
        else:
            return ["setup", "backend", "testing", "documentation"]

    def _get_domain_tasks(self, domain: str) -> List[tuple]:
        """Get domain-specific tasks."""
        domain_task_map = {
            "hospital": [
                ("Implement Patient Management", "CRUD for patient records, search, filter", 5.0, ["Patient models", "Patient API"]),
                ("Implement Appointment System", "Schedule, reschedule, cancel appointments", 4.0, ["Appointment models", "Calendar view"]),
                ("Implement Billing System", "Invoice generation, payment tracking, receipts", 5.0, ["Billing models", "Invoice API"]),
            ],
            "ecommerce": [
                ("Implement Product Catalog", "Product CRUD, categories, search, filters", 5.0, ["Product models", "Catalog API"]),
                ("Implement Shopping Cart", "Cart management, quantity updates, price calc", 3.0, ["Cart service", "Cart API"]),
                ("Implement Checkout Flow", "Address, payment, order confirmation", 6.0, ["Checkout service", "Order API"]),
            ],
            "education": [
                ("Implement Course Management", "Create/edit courses, enrollments, progress", 5.0, ["Course models", "Enrollment API"]),
                ("Implement Exam System", "Question bank, exam scheduling, auto-grading", 6.0, ["Exam models", "Exam API"]),
                ("Implement Attendance Tracking", "Mark attendance, reports, notifications", 3.0, ["Attendance models", "Attendance API"]),
            ],
        }
        return domain_task_map.get(domain, [])

    def _set_dependencies(self, tasks: List[EngineeringTask]) -> List[EngineeringTask]:
        """Set task dependencies based on category and order."""
        category_order = ["setup", "backend", "frontend", "testing", "deployment", "documentation"]
        prev_task_by_category = {}

        for task in tasks:
            cat_idx = category_order.index(task.category) if task.category in category_order else 0
            if cat_idx > 0:
                prev_cat = category_order[cat_idx - 1]
                if prev_cat in prev_task_by_category:
                    task.dependencies.append(prev_task_by_category[prev_cat])
            prev_task_by_category[task.category] = task.id

        return tasks
