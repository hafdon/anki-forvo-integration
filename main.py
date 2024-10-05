import argparse
from datetime import datetime
import sys

from anki.anki_note_card_manager import AnkiNoteManager
from anki.anki_file_manager import AnkiFileManager
from backup.backup_manager import BackupManager
from cache.cache_manager import CacheManager
from config.config import ANKI_CONNECT_URL, CACHE_FILE, DEFAULT_QUERY, RETRY_AFTER_DAYS
from config.logger import logger
from forvo.forvo_manager import ForvoManager


def parse_local_args():
    parser = argparse.ArgumentParser(
        description="Fetch Forvo pronunciations and update Anki notes based on a search query."
    )
    parser.add_argument(
        "--query",
        type=str,
        default=DEFAULT_QUERY,
        help='Anki search query (default: deck:"Default")',
    )
    parser.add_argument(
        "--retry-after-days",
        type=int,
        default=RETRY_AFTER_DAYS,
        help="Number of days to wait before retrying a failed word (default: 30)",
    )
    args = parser.parse_args()
    search_query = args.query
    retry_after_days = args.retry_after_days
    return search_query, retry_after_days


def main():

    # Initialize managers
    backup = BackupManager()
    cache_manager = CacheManager(CACHE_FILE, 500, 30)
    forvo = ForvoManager()
    anki_note_card_manager = AnkiNoteManager(ANKI_CONNECT_URL)
    anki_file_manager = AnkiFileManager(ANKI_CONNECT_URL)

    # Backup cache
    backup.limit_backups()
    backup.backup_cache()

    # Parse command-line arguments for the search query and retry configuration
    search_query, retry_after_days = parse_local_args()
    logger.info(search_query, retry_after_days)

    # Reset the request count if it's after 22:00 UTC (time set by Forvo)
    # We do this before checking the limit itself because ... logic.
    cache_manager.reset_request_count_if_new_day()

    ### Check request limit
    ### BAIL COMPLETELY if reached
    if cache_manager.is_request_limit():
        logger.warning(f"Stopping, request limit reached.")
        logger.warning("Request limit will be reset at 22:00 UTC")
        sys.exit()

    # Get the notes corresponding to our search query
    notes = anki_note_card_manager.notes_from_query(search_query)

    # filter notes by those with a "Word" field.
    # Get the value of the Word field (aka the word itself)
    filtered_words = [
        note["fields"]["Word"]["value"]
        for note in notes
        if note.get("fields", {}).get("Word", {}.get("value"))
    ]
    logger.info("Filtered words:", len(filtered_words))

    # # Check if the word is in failed_words
    # if cache.is_failed_word(word) and not cache.can_reattempt(word):
    #     logging.info(f"Skipping word '{word}'.")
    #     continue  # Skip this word
    can_attempt_words = [
        word
        for word in filtered_words
        if
        # it doesn't have any pronunciations and it doesn't have any failues
        (
            (not cache_manager.in_pronunciations(word))
            and (not cache_manager.in_failures(word))
        )
        # or it has failed, but we can reattempt
        or (cache_manager.in_failures(word) and cache_manager.can_reattempt(word))
    ]

    try:
        for word in can_attempt_words:

            # Check request limit
            # BAIL COMPLETELY if reached
            # (We do this again here because the request increment after every word.)
            if cache_manager.is_request_limit():
                logger.warning(f"Request limit reached. Bailing")
                break

            ########################
            ### FETCH PRONUNCIATIONS
            ########################

            logger.info(f"Fetching and storing pronunciations for word: '{word}'")
            response = forvo.fetch_pronunciations(word)

            filenames = []

            if response is None:
                logger.error("Something went wrong. Bailing.")
                break
            elif response["status_code"] == 400:
                logger.warning(f"Request limit reached. Bailing.")
                cache_manager.set_request_count_to_limit()
                break
            elif response["status_code"] == 200 and response["data"]:
                cache_manager.increment_request_count()
                logger.info(f"Successful fetch for: {word}")
                for item in response["data"]:
                    cache_manager.increment_request_count()
                    # Store the media file and get the filename
                    stored_filename = anki_file_manager.store_media_file(
                        item["filename"],
                        item["url"],  # format: {"filename": filename, "url": mp3_url}
                    )
                    # Keep a string of the filenames for updating the anki note
                    if stored_filename:
                        filenames.append(
                            f"sound:{stored_filename}"
                        )  # (We've removed the brackets from [sound:X] to prevent auto-play on cards)
            elif response["status_code"] == 204:
                # We received a response, but no pronunciations were available
                cache_manager.increment_request_count()
                logger.debug(f"{word}: 204")

            ########################
            ### Update Anki Cards
            ########################

            query = f'Word:"{word}"'
            notes = anki_note_card_manager.notes_from_query(query)

            for note in notes:

                note_field = "ForvoPronunciations" if filenames else "ForvoChecked"
                note_data = (
                    " ".join(filenames)
                    if filenames
                    else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )

                anki_note_card_manager.update_note_field(
                    note["noteId"], note_field, note_data
                )

            ########################
            ### Update Cache
            ########################

            cache_manager.set_last_attempt(word)
            if filenames:
                cache_manager.set_pronunciations(word, filenames)
                if cache_manager.in_failures(word):
                    cache_manager.set_unfailed(word)
            else:
                cache_manager.increment_fetch_failure(
                    word, cache_manager.get_204_error_string()
                )

    except:
        logger.exception("Exception")


if __name__ == "__main__":
    main()
