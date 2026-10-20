import os


class DocumentLoader:
    SUPPORTED_EXTENSIONS = {".md", ".markdown", ".py", ".txt", ".rst"}

    def load_file(self, path):
        with open(path, "r", encoding="utf-8") as file:
            return file.read()

    def load_directory(self, path):
        documents = []
        for root, directories, files in os.walk(path):
            directories[:] = [item for item in directories if item not in {".git", ".venv", "venv", "__pycache__"}]
            for file_name in sorted(files):
                file_path = os.path.join(root, file_name)
                if os.path.splitext(file_name)[1].casefold() not in self.SUPPORTED_EXTENSIONS:
                    continue
                try:
                    documents.append({
                        "text": self.load_file(file_path),
                        "metadata": {"source": os.path.relpath(file_path, path).replace(os.sep, "/")},
                    })
                except (OSError, UnicodeDecodeError):
                    continue
        return documents