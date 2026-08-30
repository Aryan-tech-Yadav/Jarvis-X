import json
import os
from datetime import datetime, timezone


class ArtifactManager:
    """Writes release artifacts only inside the caller-selected output root."""

    def __init__(self, output_root):
        if not isinstance(output_root, str) or not output_root.strip():
            raise ValueError("Output root cannot be empty")
        self.output_root = os.path.abspath(output_root)

    def create_release_directory(self, label=None):
        safe_label = self._safe_label(label or datetime.now(timezone.utc).strftime("release-%Y%m%dT%H%M%SZ"))
        directory = os.path.join(self.output_root, safe_label)
        os.makedirs(directory, exist_ok=True)
        return directory

    def write_json(self, directory, filename, payload):
        path = self._path(directory, filename)
        with open(path, "w", encoding="utf-8") as destination:
            json.dump(payload, destination, indent=2, sort_keys=True, default=str)
        return path

    def write_text(self, directory, filename, content):
        path = self._path(directory, filename)
        with open(path, "w", encoding="utf-8") as destination:
            destination.write(str(content).rstrip() + "\n")
        return path

    def _path(self, directory, filename):
        directory = os.path.abspath(directory)
        if os.path.commonpath((self.output_root, directory)) != self.output_root:
            raise ValueError("Artifact directory must stay inside the output root")
        name = os.path.basename(str(filename))
        if name != filename or not name or name in {".", ".."}:
            raise ValueError("Artifact filename must be a simple filename")
        os.makedirs(directory, exist_ok=True)
        return os.path.join(directory, name)

    @staticmethod
    def _safe_label(value):
        label = "".join(character if character.isalnum() or character in {"-", "_", "."} else "-" for character in str(value))
        label = label.strip(".-")
        if not label or label in {".", ".."}:
            raise ValueError("Release label is invalid")
        return label
