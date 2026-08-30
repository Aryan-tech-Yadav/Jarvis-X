import os

from app.knowledge.cache import KnowledgeCache
from app.knowledge.document_loader import DocumentLoader
from app.knowledge.file_indexer import FileIndexer
from app.knowledge.knowledge_manager import KnowledgeManager


class ProjectIndexer:
    def __init__(self, knowledge_manager=None, loader=None, cache=None):
        self.knowledge = knowledge_manager or KnowledgeManager()
        self.loader = loader or DocumentLoader()
        self.cache = cache or KnowledgeCache()
        self.files = FileIndexer(self.knowledge, self.loader, self.cache)

    def index(self, base_path):
        base_path = os.path.abspath(base_path)
        indexed = []
        current_sources = set()
        for item in self.loader.load_directory(base_path):
            source = os.path.abspath(os.path.join(base_path, item["metadata"]["source"]))
            current_sources.add(source)
            result = self.files.index_file(source, project=base_path)
            if result["indexed"]:
                indexed.append(source)

        stale = [source for source, entry in list(self.cache.entries.items())
                 if entry.get("project") == base_path and source not in current_sources]
        for source in stale:
            self.knowledge.store.remove_by_metadata("source", source)
            self.cache.remove(source)
        return indexed