import json


class SemanticExport:
    def export(self, memories, statistics):
        return {"memories": [memory.to_dict() for memory in memories], "statistics": dict(statistics)}

    def to_json(self, memories, statistics):
        return json.dumps(self.export(memories, statistics), indent=2, sort_keys=True)
