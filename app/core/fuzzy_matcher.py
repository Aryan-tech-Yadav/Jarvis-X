from difflib import SequenceMatcher


class FuzzyMatcher:

    @staticmethod
    def similarity(a, b):

        return SequenceMatcher(None, a, b).ratio()