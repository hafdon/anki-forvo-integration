import argparse
from datetime import datetime
import sys

from anki.anki_invoker import AnkiInvoker
from anki.anki_note_card_manager import AnkiNoteCardManager
from anki.anki_pronunciations_manager import AnkiPronunciationsManager
from anki.anki_file_manager import AnkiFileManager
from backup.backup_manager import BackupManager
from cache.cache_manager import CacheManager
from config.config import ANKI_CONNECT_URL, CACHE_FILE, RETRY_AFTER_DAYS
from config.logger import logger
from forvo.forvo_manager import ForvoManager

# from fetch_forvo_pronunciations import main as forvo_main

DEFAULT_QUERY = 'deck:"nouns"'


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

    # print("Logging to log file.")
    backup = BackupManager()

    backup.limit_backups()
    backup.backup_cache()

    # Parse command-line arguments for the search query and retry configuration
    search_query, retry_after_days = parse_local_args()
    print(search_query, retry_after_days)

    cache_manager = CacheManager(CACHE_FILE, 500, 30)

    note_card_manager = AnkiNoteCardManager(ANKI_CONNECT_URL)
    anki_note_card_manager = AnkiNoteCardManager(ANKI_CONNECT_URL)
    forvo = ForvoManager()

    cache_manager.reset_request_count_if_new_day()

    ### Check request limit
    ### BAIL COMPLETELY if reached
    if cache_manager.is_request_limit():
        logger.warning(f"Stopping, request limit reached.")
        logger.info("Request limit will be reset at 22:00 UTC")
        sys.exit()

    notes = note_card_manager.notes_from_query(search_query)
    print(notes)

    # filter notes by those with a "Word" field.
    # Get the value of the Word field (aka the word itself)
    filtered_words = [
        note["fields"]["Word"]["value"]
        for note in notes
        if note.get("fields", {}).get("Word", {}.get("value"))
    ]
    print(filtered_words)  # []'struchtúr']

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

            ### Check request limit
            ### BAIL COMPLETELY if reached
            if cache_manager.is_request_limit():
                logger.warning(f"Stopping, request limit reached.")
                break
            logger.info("Request limit not reached. Continuing.")

            ###
            ### FETCH PRONUNCIATIONS
            ###

            logger.info(f"Fetching and storing pronunciations for word: '{word}'")
            response = forvo.fetch_pronunciations(word)
            logger.info(response)

            filenames = []

            if response is None:
                # something went really wrong
                logger.error("Something went wrong. Breaking.")
                break
            elif response["status_code"] == 400:
                try:
                    cache_manager.set_request_count_to_limit()  # passing with no argument sets to limit
                    logger.warning(f"Stopping, request limit reached.")
                    break

                except Exception as e:
                    logger.exception(e)
                pass
            elif response["status_code"] == 200 and response["data"]:
                # We got some mp3 urls
                # format: {"filename": filename, "url": mp3_url}

                # Store the media file in Anki
                anki_file_manager = AnkiFileManager(ANKI_CONNECT_URL)

                for item in response["data"]:
                    # May need to move where this is, depending on what counts as request
                    cache_manager.increment_request_count()
                    stored_filename = anki_file_manager.store_media_file(
                        item["filename"], item["url"]
                    )
                    if stored_filename:
                        filenames.append(f"[sound:{stored_filename}]")
            elif response["status_code"] == 204:
                # We received a response, but no pronunciations were available
                try:
                    cache_manager.increment_request_count()  # This counts, yikes!
                    cache_manager.increment_fetch_failure(
                        word, cache_manager.get_204_error_string()
                    )
                    cache_manager.set_last_attempt(word)

                    # Update anki note with date of failed attempt
                    query = f'Word:"{word}"'
                    notes = anki_note_card_manager.notes_from_query(query)

                    for note in notes:
                        anki_note_card_manager.update_note_field(
                            note["noteId"],
                            "ForvoChecked",
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        )

                except Exception as e:
                    logger.exception(e)

            ###
            # Now that we got mp3s, and the filenames of where they were downloaded to,
            # 1. Update the anki notes with the filenames in the ForvoPronunciations field.
            # 2. Update the cache
            ###
            if filenames:

                # 1. Update anki cards

                query = f'Word:"{word}"'
                notes = anki_note_card_manager.notes_from_query(query)

                for note in notes:
                    anki_note_card_manager.update_note_field(
                        note["noteId"], "ForvoPronunciations", " ".join(filenames)
                    )

                # 2. Update cache with:
                #    - pronunciations
                #    - increased request attempt total
                # 3. Clear record of failed word
                cache_manager.set_pronunciations(word, filenames)
                cache_manager.set_last_attempt(word)
                if cache_manager.in_failures(word):
                    cache_manager.set_unfailed(word)

    except:
        logger.error("Exception")

    ### It's possible to have conflicting information, if it's in both failed_words and pronunciations
    ### but this means something messed up earlier, and has more to do with data consistency

    print(can_attempt_words)


if __name__ == "__main__":
    main()
