import json
import os
import uuid

from app.knowledge.embedding_manager import EmbeddingManager
from config import KNOWLEDGE_PATH


class VectorStore:
    def __init__(self, path=None, embedding_manager=None):
        self.path = path or KNOWLEDGE_PATH
        self.embedding_manager = embedding_manager or EmbeddingManager()
        self.documents = {}
        self._load()

    def add(self, text, metadata=None, document_id=None):
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Document text cannot be empty")
        content = text.strip()
        for document in self.documents.values():
            if document["text"] == content:
                return document["id"]

        document_id = document_id or str(uuid.uuid4())
        document = {
            "id": document_id,
            "text": content,
            "metadata": dict(metadata or {}),
            "embedding": self.embedding_manager.embed(content),
        }
        self.documents[document_id] = document
        self.save()
        return document_id

    def search(self, query, limit=5, threshold=0.0):
        query_embedding = self.embedding_manager.embed(query)
        matches = [
            (self.embedding_manager.similarity(query_embedding, document["embedding"]), document)
            for document in self.documents.values()
        ]
        matches = [(score, document) for score, document in matches if score >= threshold]
        matches.sort(key=lambda item: item[0], reverse=True)
        return [{"score": score, **self._public(document)} for score, document in matches[:max(0, limit)]]

    def save(self):
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(list(self.documents.values()), file, indent=2)

    def remove_by_metadata(self, key, value):
        removed = [document_id for document_id, document in self.documents.items()
                   if document.get("metadata", {}).get(key) == value]
        for document_id in removed:
            del self.documents[document_id]
        if removed:
            self.save()
        return len(removed)

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                documents = json.load(file)
        except (OSError, json.JSONDecodeError):
            return
        if isinstance(documents, list):
            for document in documents:
                if isinstance(document, dict) and document.get("id") and document.get("text"):
                    document.setdefault("embedding", self.embedding_manager.embed(document["text"]))
                    document.setdefault("metadata", {})
                    self.documents[document["id"]] = document

    def _public(self, document):
        return {key: document[key] for key in ("id", "text", "metadata")}