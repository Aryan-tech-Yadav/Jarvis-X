class RequirementClarifier:
    ROLE_PRODUCTS = ("hospital", "crm", "erp", "school", "restaurant", "ecommerce", "e-commerce")

    def clarify(self, goal, requirements, existing=None):
        value = str(goal or "").casefold()
        existing = existing or {}
        questions = list(existing.get("clarifying_questions", ()))
        missing = list(existing.get("ambiguities", ()))
        if any(product in value for product in self.ROLE_PRODUCTS) and not any(word in value for word in ("role", "admin", "staff", "user")):
            questions.append("Which user roles and permissions are required?")
            missing.append("User roles and permissions are unspecified.")
        non_functional = getattr(requirements, "non_functional", [])
        if "deployment" not in non_functional:
            questions.append("Should the first release include Docker and CI/CD deployment configuration?")
        if "api" not in value and "web" not in value and "website" not in value:
            questions.append("Should this expose a REST API, a web interface, or both?")
        requirements.missing = sorted(set(missing))
        requirements.questions = list(dict.fromkeys(questions))
        return requirements
