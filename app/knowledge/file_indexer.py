import hashlib
import os

from app.knowledge.cache import KnowledgeCache
from app.knowledge.document_loader import DocumentLoader
from app.knowledge.knowledge_manager import KnowledgeManager


class FileIndexer:
    def __init__(self, knowledge_manager=None, loader=None, cache=None):
        self.knowledge = knowledge_manager or KnowledgeManager()
        self.loader = loader or DocumentLoader()
        self.cache = cache or KnowledgeCache()

    def index_file(self, path, project=None):
        source = os.path.abspath(path)
        text = self.loader.load_file(source)
        signature = hashlib.sha256(text.encode("utf-8")).hexdigest()
        cached = self.cache.get(source)
        if cached and cached.get("signature") == signature:
            return {"indexed": False, "changed": False, "document_id": cached.get("document_id")}

        metadata = {"source": source, "type": "file"}
        if project:
            metadata["project"] = os.path.abspath(project)
        old_id = cached.get("document_id") if cached else None
        if old_id:
            self.knowledge.store.remove_by_metadata("source", source)
        document_id = self.knowledge.add_document(text, metadata)
        self.cache.set(source, signature, document_id, project)
        return {"indexed": True, "changed": bool(cached), "document_id": document_id}