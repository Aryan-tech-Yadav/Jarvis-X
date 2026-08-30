class DatabaseDesigner:
    BASE = ["users"]
    FEATURE_ENTITIES = {
        "profiles": ["profiles"], "posts": ["posts"], "comments": ["comments"], "payments": ["payments", "orders", "products"],
        "uploads": ["uploads"], "notifications": ["notifications"], "realtime": ["conversations", "messages"],
        "admin": ["audit_logs"],
        "appointments": ["appointments"], "billing": ["invoices"], "reports": ["reports"],
        "reservations": ["reservations"], "orders": ["orders"],
    }
    PRODUCT_ENTITIES = {
        "hospital": ["hospitals", "patients", "doctors", "appointments", "invoices"],
        "ecommerce": ["products", "categories", "carts", "orders", "payments"],
        "e-commerce": ["products", "categories", "carts", "orders", "payments"],
        "restaurant": ["tables", "menus", "reservations", "orders"],
    }

    def design(self, goal, requirements):
        entities = list(self.BASE)
        for feature in requirements.functional:
            entities.extend(self.FEATURE_ENTITIES.get(feature, ()))
        value = str(goal).casefold()
        for product, values in self.PRODUCT_ENTITIES.items():
            if product in value:
                entities.extend(values)
        entities = list(dict.fromkeys(entities))
        relationships = [{"from": "users", "to": entity, "type": "owns"} for entity in entities if entity not in {"users", "products", "categories"}]
        if "orders" in entities and "products" in entities:
            relationships.append({"from": "orders", "to": "products", "type": "contains"})
        return {"entities": entities, "relationships": relationships}
