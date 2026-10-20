import os
from app.context.context_builder import ContextBuilder
from app.context.context_summary import ContextSummary
from app.context.context_window import ContextWindow


class ContextManager:

    def __init__(self, max_file_chars=6000, builder=None, window=None, summarizer=None):
        self.max_file_chars = max_file_chars
        self.builder = builder or ContextBuilder()
        self.window = window or ContextWindow()
        self.summarizer = summarizer or ContextSummary()

    def build(self, goal, current_project=None, current_step="", conversation=None,
              reasoning=None, progress=None, plan=None, project_summary=None):
        context = self.builder.build(goal, current_project, current_step, conversation,
                                     reasoning, progress, plan, project_summary)
        context["summary"] = self.summarizer.summarize(
            context["conversation"] + context["reasoning"]
        )["summary"]
        return self.window.apply(context)

    def get_context(self, project, current_file, base_path):
        current_name = current_file["name"] if isinstance(current_file, dict) else current_file
        context_parts = []

        for file_info in project.get("files", []):
            file_name = file_info.get("name", "")
            if file_name == current_name:
                continue

            file_path = os.path.join(base_path, file_name)
            if not os.path.isfile(file_path):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read(self.max_file_chars)
            except (OSError, UnicodeDecodeError):
                continue

            if not content.strip():
                continue

            context_parts.append(f"File: {file_name}\n{content}")

        return "\n\n".join(context_parts) or "No other project files have been generated yet."
