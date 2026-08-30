from collections import Counter


class SemanticStatistics:
    def calculate(self, memories):
        memories = list(memories)
        types = Counter(memory.memory_type for memory in memories)
        tags = Counter(tag for memory in memories for tag in memory.tags)
        return {
            "count": len(memories),
            "by_type": dict(sorted(types.items())),
            "top_tags": [tag for tag, _ in tags.most_common(5)],
            "average_importance": round(sum(memory.importance for memory in memories) / len(memories), 3)
            if memories else 0.0,
        }
