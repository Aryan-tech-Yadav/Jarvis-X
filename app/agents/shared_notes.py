class SharedNotes:
    def __init__(self):
        self._notes = {}

    def write(self, author, note):
        self._notes.setdefault(author, []).append(note)

    def read(self, author=None):
        if author is None:
            return {key: list(value) for key, value in self._notes.items()}
        return list(self._notes.get(author, []))