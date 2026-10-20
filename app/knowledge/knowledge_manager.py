from app.knowledge.document_loader import DocumentLoader
from app.knowledge.vector_store import VectorStore
from app.core.logger import Logger


class KnowledgeManager:
    def __init__(self, vector_store=None, document_loader=None):
        self.store = vector_store or VectorStore()
        self.loader = document_loader or DocumentLoader()
        self.semantic_base = None

    def add_document(self, text, metadata=None):
        return self.store.add(text, metadata)

    def add_documents(self, documents):
        ids = []
        for document in documents:
            if isinstance(document, str):
                ids.append(self.add_document(document))
            else:
                ids.append(self.add_document(document["text"], document.get("metadata")))
        return ids

    def search(self, query, limit=5, threshold=0.0):
        return self.store.search(query, limit, threshold)

    def index_project(self, base_path):
        from app.knowledge.project_indexer import ProjectIndexer

        indexed = ProjectIndexer(self, self.loader).index(base_path)
        Logger.info(f"Indexed {len(indexed)} changed knowledge documents from {base_path}")
        return indexed

    def retrieve_similar(self, text, limit=5):
        return self.search(text, limit=limit)

    def add_fact(self, text, **kwargs):
        """Add a categorized fact without changing the document-vector API."""
        if self.semantic_base is None:
            from app.knowledge.knowledge_base import KnowledgeBase
            self.semantic_base = KnowledgeBase()
        return self.semantic_base.add_fact(text, **kwargs)

    def search_facts(self, query, limit=5):
        return self.semantic_base.search(query, limit) if self.semantic_base else []
