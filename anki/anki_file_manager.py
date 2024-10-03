from anki.anki_invoker import AnkiInvoker
from config.config import AUDIO_FILE_PATTERN, MEDIA_DIR

import os
import re
from config.logger import logger


class AnkiFileManager:
    def __init__(self, ANKI_CONNECT_URL) -> None:
        self.invoker = AnkiInvoker(ANKI_CONNECT_URL)
        pass

    def get_media_files(self):
        """Retrieve all relevant audio files from the media directory."""
        files = os.listdir(MEDIA_DIR)

        if MEDIA_DIR is None:
            logger.critical("MEDIA_DIR is not defined.")

        audio_files = [f for f in files if re.match(AUDIO_FILE_PATTERN, f)]
        return audio_files

    def extract_word(self, filename):
        """Extract the word from the filename using regex."""
        match = re.match(AUDIO_FILE_PATTERN, filename)
        if match:
            return match.group(1)
        return None

    def store_media_file(self, filename, url):
        logger.info(
            f"AnkiFileManager: Attempting to retrieve media file {url} as {filename}"
        )
        try:
            store_response = self.invoker.invoke(
                "storeMediaFile", {"filename": filename, "url": url}
            )
            if "error" in store_response and store_response["error"]:
                logger.error(
                    f"Error storing media file '{filename}': {store_response['error']}"
                )
                return None
            stored_filename = store_response.get("result")
            logger.info(f"Stored media file '{stored_filename}'.")
            return stored_filename
        except Exception as e:
            logger.exception("Exception trying to store files")
