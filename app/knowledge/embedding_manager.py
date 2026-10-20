import math
import re
from collections import Counter


class EmbeddingManager:
    TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")

    def embed(self, text):
        if not isinstance(text, str):
            raise TypeError("Text must be a string")
        return dict(Counter(token.casefold() for token in self.TOKEN_PATTERN.findall(text)))

    def similarity(self, left, right):
        if not left or not right:
            return 0.0
        common = set(left) & set(right)
        numerator = sum(left[token] * right[token] for token in common)
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        return numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0