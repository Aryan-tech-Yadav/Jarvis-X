from app.reasoning.observation import Observation


class ObservationManager:
    def normalize(self, result, tool="", action=""):
        if isinstance(result, Observation):
            return result
        if not isinstance(result, dict):
            return Observation(False, result, "Tool returned an invalid result", tool, action)
        return Observation(bool(result.get("success")), result.get("output", result.get("message")),
                           result.get("error"), tool, action, changed_files=result.get("changed_files", []),
                           validation=result.get("validation"), warnings=result.get("warnings", []))