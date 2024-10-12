# application.py
import argparse
import sys
import logging
from datetime import datetime

from factories import ManagerFactory
from commands import WordProcessingCommand
from config.logger import logger


class Application:
    def __init__(self, args=None):
        try:
            self.backup_manager = ManagerFactory.create_backup_manager()
            self.cache_manager = ManagerFactory.create_cache_manager()
            self.forvo_manager = ManagerFactory.create_forvo_manager()
            self.anki_note_card_manager = ManagerFactory.create_anki_note_card_manager()
            self.anki_file_manager = ManagerFactory.create_anki_file_manager()

        except ConnectionError as e:
            logger.error("Unable to establish a connection with AnkiConnect.")
            logger.error(
                "Please ensure that Anki is running and that the AnkiConnect add-on is installed and enabled."
            )
            logger.error(
                "Refer to https://ankiweb.net/shared/info/2055492159 for installation instructions."
            )
            sys.exit(1)

        self.search_query, self.retry_after_days = self.parse_args(args)

    def parse_args(self, args):
        parser = argparse.ArgumentParser(
            description="Fetch Forvo pronunciations and update Anki notes based on a search query."
        )
        parser.add_argument(
            "--query",
            type=str,
            default='deck:"Default"',
            help='Anki search query (default: deck:"Default")',
        )
        parser.add_argument(
            "--retry-after-days",
            type=int,
            default=30,
            help="Number of days to wait before retrying a failed word (default: 30)",
        )
        parsed_args = parser.parse_args(args)
        return parsed_args.query, parsed_args.retry_after_days

    def setup(self):
        # Backup cache
        self.backup_manager.limit_backups()
        self.backup_manager.backup_cache()

        # Log the parsed arguments
        logger.info(
            f"Search Query: {self.search_query}, Retry After Days: {self.retry_after_days}"
        )

        # Reset request count if it's a new day
        self.cache_manager.reset_request_count_if_new_day()

    def run(self):
        self.setup()

        # Check request limit
        if self.cache_manager.is_request_limit():
            logger.warning("Stopping, request limit reached.")
            logger.warning("Request limit will be reset at 22:00 UTC")
            sys.exit()

        # Get and filter notes
        notes = self.anki_note_card_manager.notes_from_query(self.search_query)
        filtered_words = [
            note["fields"]["Word"]["value"]
            for note in notes
            if note.get("fields", {}).get("Word", {}).get("value")
        ]
        logger.info(f"Filtered words: {len(filtered_words)}")

        # Determine which words can be attempted
        can_attempt_words = [
            word
            for word in set(filtered_words)
            if (
                (
                    not self.cache_manager.in_pronunciations(word)
                    and not self.cache_manager.in_failures(word)
                )
                or (
                    self.cache_manager.in_failures(word)
                    and self.cache_manager.can_reattempt(word)
                )
            )
        ]

        logger.info(f"Words to attempt: {len(can_attempt_words)}")

        try:
            for word in can_attempt_words:
                if self.cache_manager.is_request_limit():
                    logger.warning("Request limit reached. Bailing.")
                    break

                command = WordProcessingCommand(
                    word,
                    self.forvo_manager,
                    self.anki_note_card_manager,
                    self.anki_file_manager,
                    self.cache_manager,
                )
                command.execute()

        except Exception as e:
            logger.exception(f"An unexpected exception occurred: {e}")
