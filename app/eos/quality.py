from typing import Any, Dict


class QualityGate:
    def evaluate(self, context: Any) -> Dict[str, Any]:
        errors = list(getattr(context, "errors", []))
        score = max(0.0, 100.0 - len(errors) * 10.0)
        return {"passed": not errors, "score": score, "errors": errors}
