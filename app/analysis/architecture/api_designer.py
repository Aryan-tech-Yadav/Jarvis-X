class APIDesigner:
    FEATURE_ENDPOINTS = {
        "authentication": [("POST", "/auth/signup"), ("POST", "/auth/login")],
        "profiles": [("GET", "/profiles/{id}"), ("PUT", "/profile")],
        "posts": [("GET", "/posts"), ("POST", "/posts")],
        "comments": [("POST", "/posts/{id}/comments")],
        "search": [("GET", "/search")],
        "payments": [("POST", "/checkout"), ("GET", "/orders")],
        "uploads": [("POST", "/uploads")],
        "notifications": [("GET", "/notifications")],
        "admin": [("GET", "/admin/health")],
        "appointments": [("GET", "/appointments"), ("POST", "/appointments")],
        "billing": [("GET", "/invoices"), ("POST", "/invoices")],
        "reports": [("GET", "/reports")],
        "reservations": [("GET", "/reservations"), ("POST", "/reservations")],
        "orders": [("GET", "/orders"), ("POST", "/orders")],
    }

    def design(self, requirements):
        endpoints = [{"method": "GET", "path": "/health", "purpose": "service health"}]
        for feature in requirements.functional:
            endpoints.extend({"method": method, "path": path, "purpose": feature} for method, path in self.FEATURE_ENDPOINTS.get(feature, ()))
        return {"endpoints": endpoints}
