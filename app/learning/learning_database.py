import hashlib
import json


class LearningDatabase:
    def __init__(self):
        self.records = []
        self._fingerprints = set()

    def record(self, outcome):
        if not isinstance(outcome, dict) or not outcome.get("area"):
            raise ValueError("Learning outcome requires an area")
        fingerprint = hashlib.sha256(json.dumps(outcome, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        if fingerprint in self._fingerprints:
            return False
        stored = dict(outcome)
        stored["fingerprint"] = fingerprint
        self.records.append(stored)
        self._fingerprints.add(fingerprint)
        return True

    def count(self):
        return len(self.records)

    def by_area(self):
        groups = {}
        for record in self.records:
            groups.setdefault(record["area"], []).append(record)
        return groups
