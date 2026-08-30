from app.benchmark.golden_project import GoldenProject


class GoldenBenchmarkSuite:
    """The release benchmark catalog; no project is generated at import time."""

    PROJECTS = (
        GoldenProject("calculator", "Calculator", "Build a calculator application with core calculation workflows", "basic", ("core",)),
        GoldenProject("todo-api", "Todo API", "Build a Todo API with login, search, and an admin dashboard", "basic", ("authentication", "search", "admin")),
        GoldenProject("notes-app", "Notes App", "Build a notes application with login, search, and file uploads", "basic", ("authentication", "search", "uploads")),
        GoldenProject("blog", "Blog", "Build a blog application with login, posts, comments, search, and an admin dashboard", "basic", ("authentication", "posts", "comments", "search", "admin")),
        GoldenProject("crm", "CRM", "Build a CRM application with login, customer profiles, search, reports, and an admin dashboard", "intermediate", ("authentication", "profiles", "search", "admin")),
        GoldenProject("chat-app", "Chat App", "Build a chat application with login, realtime messaging, notifications, and profiles", "intermediate", ("authentication", "realtime", "notifications", "profiles")),
        GoldenProject("school-erp", "School ERP", "Build a school ERP with login, student profiles, search, reports, and an admin dashboard", "intermediate", ("authentication", "profiles", "search", "admin")),
        GoldenProject("inventory", "Inventory", "Build an inventory application with login, search, uploads, reports, and an admin dashboard", "intermediate", ("authentication", "search", "uploads", "admin")),
        GoldenProject("cms", "CMS", "Build a CMS with login, posts, uploads, search, comments, and an admin dashboard", "intermediate", ("authentication", "posts", "uploads", "search", "comments", "admin")),
        GoldenProject("hrms", "HRMS", "Build an HRMS with login, employee profiles, search, notifications, and an admin dashboard", "intermediate", ("authentication", "profiles", "search", "notifications", "admin")),
        GoldenProject("hospital", "Hospital Management", "Build a hospital management application with login, patient profiles, search, uploads, notifications, and an admin dashboard", "advanced", ("authentication", "profiles", "search", "uploads", "notifications", "admin")),
        GoldenProject("ecommerce", "E-commerce", "Build an e-commerce application with login, checkout payments, search, uploads, profiles, and an admin dashboard", "advanced", ("authentication", "payments", "search", "uploads", "profiles", "admin"), True),
        GoldenProject("banking", "Banking", "Build a banking application with login, payment transfers, profiles, notifications, reports, and an admin dashboard", "advanced", ("authentication", "payments", "profiles", "notifications", "admin"), True),
        GoldenProject("lms", "Learning Management System", "Build an LMS with login, student profiles, posts, uploads, search, notifications, and an admin dashboard", "advanced", ("authentication", "profiles", "posts", "uploads", "search", "notifications", "admin")),
        GoldenProject("social-network", "Social Network", "Build a social network with login, profiles, posts, comments, uploads, search, and notifications", "advanced", ("authentication", "profiles", "posts", "comments", "uploads", "search", "notifications")),
        GoldenProject("ai-saas", "AI SaaS", "Build an AI SaaS application with login, payments, profiles, search, notifications, and an admin dashboard", "expert", ("authentication", "payments", "profiles", "search", "notifications", "admin"), True),
        GoldenProject("multi-agent", "Multi-Agent Platform", "Build a multi-agent platform with login, realtime notifications, search, reports, and an admin dashboard", "expert", ("authentication", "realtime", "notifications", "search", "admin")),
        GoldenProject("vscode-extension", "VS Code Extension", "Build a VS Code extension with login, search, notifications, and an admin dashboard", "expert", ("authentication", "search", "notifications", "admin")),
        GoldenProject("file-sync", "File Sync Tool", "Build a file synchronization application with login, profiles, file uploads, search, notifications, and an admin dashboard", "expert", ("authentication", "profiles", "uploads", "search", "notifications", "admin")),
        GoldenProject("project-management", "Project Management Tool", "Build a project management application with login, profiles, posts, comments, search, notifications, and an admin dashboard", "expert", ("authentication", "profiles", "posts", "comments", "search", "notifications", "admin")),
    )

    def projects(self, tier=None):
        if tier is None:
            return list(self.PROJECTS)
        return [project for project in self.PROJECTS if project.tier == str(tier).casefold()]

    def get(self, identifier):
        normalized = str(identifier).casefold()
        return next((project for project in self.PROJECTS if project.identifier == normalized), None)

    def tiers(self):
        return {tier: self.projects(tier) for tier in ("basic", "intermediate", "advanced", "expert")}
