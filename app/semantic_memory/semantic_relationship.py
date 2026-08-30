class SemanticRelationship:
    """Infers transparent relationships from shared tags and memory type."""

    def related(self, memory, candidates, limit=5):
        relationships = []
        memory_tags = set(memory.tags)
        for candidate in candidates:
            if candidate.memory_id == memory.memory_id:
                continue
            shared_tags = sorted(memory_tags.intersection(candidate.tags))
            if not shared_tags and candidate.memory_type != memory.memory_type:
                continue
            strength = len(shared_tags) + (0.25 if candidate.memory_type == memory.memory_type else 0)
            relationships.append({
                "id": candidate.memory_id,
                "relationship": "shared_tags" if shared_tags else "same_type",
                "shared_tags": shared_tags,
                "strength": strength,
            })
        relationships.sort(key=lambda item: (item["strength"], item["id"]), reverse=True)
        return relationships[:limit]
