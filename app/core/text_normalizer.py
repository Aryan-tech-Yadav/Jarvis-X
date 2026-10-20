import re


class TextNormalizer:

    @staticmethod
    def normalize(text: str) -> str:

        text = text.lower()

        text = re.sub(r"[^\w\s]", "", text)

        text = " ".join(text.split())

        return text