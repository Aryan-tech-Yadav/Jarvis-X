from app.core.logger import Logger
from app.memory.memory_manager import MemoryManager
from app.intent.intent_classifier import IntentClassifier
from app.project.project_manager import ProjectManager
from app.router.tool_router import ToolRouter


class JarvisCLI:

    def __init__(self, manager=None, memory=None, classifier=None, router=None):
        self.manager = manager or ProjectManager()
        self.memory = memory or MemoryManager()
        self.classifier = classifier or IntentClassifier()
        self.router = router or ToolRouter(self.manager)
        self.current_project = None

    def handle_command(self, command):
        command = command.strip()
        if not command:
            return True

        classification = self.classifier.classify(command)
        intent = classification["intent"]
        request = classification["request"]

        if intent == "EXIT":
            self.memory.add_message("user", command)
            return False

        self.memory.add_message("user", command)
        request, project = self._prepare_request(intent, request)
        routed = self.router.route(intent, request, project)
        self.current_project = routed.get("current_project", self.current_project)
        result = routed.get("result")
        self.memory.add_message("assistant", f"{routed['action']}: {result}")
        Logger.info(result)
        return True

    def _prepare_request(self, intent, request):
        if intent == "CREATE_PROJECT":
            parts = request.split(maxsplit=1)
            if len(parts) == 2 and parts[0].lower() in {"create", "build"}:
                return parts[1], self.current_project
            return request, self.current_project

        if intent != "MODIFY_PROJECT":
            return request, self.current_project

        parts = request.split(maxsplit=1)
        if len(parts) == 2 and parts[0].lower() == "modify":
            request = parts[1]

        parts = request.split(maxsplit=1)
        if len(parts) == 2 and parts[0].lower().replace("\\", "/").startswith("workspace/"):
            return parts[1], parts[0]
        return request, self.current_project

    def run(self):
        while True:
            try:
                command = input("Jarvis > ")
            except (EOFError, KeyboardInterrupt):
                Logger.warning("Shutting down...")
                break

            if not self.handle_command(command):
                break


if __name__ == "__main__":
    JarvisCLI().run()
