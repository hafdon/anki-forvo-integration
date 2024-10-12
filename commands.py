# commands.py
import logging
from datetime import datetime


class WordProcessingCommand:
    def __init__(
        self, word, forvo_manager, anki_note_manager, anki_file_manager, cache_manager
    ):
        self.word = word
        self.forvo_manager = forvo_manager
        self.anki_note_manager = anki_note_manager
        self.anki_file_manager = anki_file_manager
        self.cache_manager = cache_manager
        self.logger = logging.getLogger(__name__)

    def execute(self):
        try:
            self.logger.debug(f"Attempting to fetch pronunciations for '{self.word}'")
            response = self.forvo_manager.fetch_pronunciations(self.word)
            filenames = []

            if response is None:
                self.logger.error("Something went wrong. Skipping word.")
                return
            elif response["status_code"] == 400:
                self.logger.warning(
                    "Request limit reached. Stopping further processing."
                )
                self.cache_manager.set_request_count_to_limit()
                return
            elif response["status_code"] == 200 and response["data"]:
                self.cache_manager.increment_request_count()
                self.logger.debug(f"[200] Successful fetch for: {self.word}")
                for item in response["data"]:
                    self.cache_manager.increment_request_count()
                    stored_filename = self.anki_file_manager.store_media_file(
                        item["filename"],
                        item["url"],
                    )
                    if stored_filename:
                        filenames.append(f"sound:{stored_filename}")
            elif response["status_code"] == 204:
                self.cache_manager.increment_request_count()
                self.logger.debug(f"[204] No pronunciations found for: {self.word}")

            # Update Anki Cards
            query = f'Word:"{self.word}"'
            notes = self.anki_note_manager.notes_from_query(query)

            for note in notes:
                note_field = "ForvoPronunciations" if filenames else "ForvoChecked"
                note_data = (
                    " ".join(filenames)
                    if filenames
                    else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                self.anki_note_manager.update_note_field(
                    note["noteId"], note_field, note_data
                )

            # Update Cache
            self.cache_manager.set_last_attempt(self.word)
            if filenames:
                self.cache_manager.set_pronunciations(self.word, filenames)
                if self.cache_manager.in_failures(self.word):
                    self.cache_manager.set_unfailed(self.word)
            else:
                self.cache_manager.increment_fetch_failure(
                    self.word, self.cache_manager.get_204_error_string()
                )

        except Exception as e:
            self.logger.exception(
                f"Exception occurred while processing word '{self.word}': {e}"
            )
