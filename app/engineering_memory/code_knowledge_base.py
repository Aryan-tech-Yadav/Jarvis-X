"""Content-addressed index of reusable source files."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CodeFingerprint:
    path: str
    digest: str
    features: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {"path": self.path, "digest": self.digest, "features": list(self.features),
                "dependencies": list(self.dependencies), "quality_score": self.quality_score,
                "metadata": dict(self.metadata)}


class CodeKnowledgeBase:
    def __init__(self):
        self._files: Dict[str, CodeFingerprint] = {}
        self._by_digest: Dict[str, str] = {}

    def index(self, path: str, content: str, features=None, dependencies=None,
              quality_score: float = 0.0, metadata=None) -> CodeFingerprint:
        if not path or not path.strip():
            raise ValueError("Code path cannot be empty")
        if not isinstance(content, str):
            raise TypeError("Code content must be a string")
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        fingerprint = CodeFingerprint(path.strip(), digest, list(features or []),
                                      list(dependencies or []), float(quality_score),
                                      dict(metadata or {}))
        self._files[fingerprint.path] = fingerprint
        self._by_digest[digest] = fingerprint.path
        return fingerprint

    def get(self, path: str) -> Optional[CodeFingerprint]:
        return self._files.get(path)

    def find_by_content(self, content: str) -> Optional[CodeFingerprint]:
        return self._files.get(self._by_digest.get(hashlib.sha256(content.encode("utf-8")).hexdigest(), ""))

    def all(self) -> List[CodeFingerprint]:
        return list(self._files.values())

