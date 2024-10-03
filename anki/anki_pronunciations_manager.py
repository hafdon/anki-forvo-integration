class AnkiPronunciationsManager:
    def __init__(self):
        self.pronunciations_buffer = {}

    def is_buffer_empty(self):
        return not self.pronunciations_buffer

    def write_to_buffer(self, word, pronunciations):
        if word and pronunciations:
            self.pronunciations_buffer[word] = pronunciations
            return True
        return False

    def get_buffer(self):
        return self.pronunciations_buffer

    def flush_buffer(self):
        raise NotImplementedError(
            "AnkiPronunciationsManager.flush_buffer is not implemented yet."
        )
