import os
import time
import argparse
from datetime import datetime, timedelta

import logging

from anki_helper import get_cards, get_notes, update_anki_notes
from cache.cache_manager import CacheManager
from cache_helper import load_cache, reset_request_count_if_new_day, save_cache
from forvo_helper import ForvoManager, fetch_and_store_pronunciations

# Configuration
ANKI_CONNECT_URL = os.getenv("ANKI_CONNECT_URL", "http://localhost:8765")
FORVO_API_KEY = os.getenv("FORVO_API_KEY")  # Replace with your actual Forvo API key
FORVO_LANGUAGE = os.getenv("FORVO_LANGUAGE", "en")  # Default to English
DEFAULT_QUERY = os.getenv(
    "ANKI_SEARCH_QUERY", 'deck:"Default"'
)  # Default query if none provided
MODEL_NAME = os.getenv("MODEL_NAME", "Basic")
FIELD_NAME = os.getenv("FIELD_NAME", "ForvoPronunciations")
CACHE_FILE = os.getenv("CACHE_FILE", "cache.json")  # File to store cached data

# Forvo API limit
DAILY_REQUEST_LIMIT = 500  # Adjust based on Forvo's rate limits
RETRY_AFTER_DAYS = 31


def main():
    # Parse command-line arguments for the search query and retry configuration
    search_query, retry_after_days = parse_local_args()

    cache = CacheManager(CACHE_FILE, DAILY_REQUEST_LIMIT, retry_after_days)
    anki = AnkiManager()
    forvo = ForvoManager()

    # Load cache
    cache.load_cache(CACHE_FILE)

    # Reset request count if a new day
    cache.reset_request_count_if_new_day()

    notes = anki.notes_from_query(search_query)
    if not notes:
        logging.info("No notes found. Exiting.")
        return
    # If note has no "Word" field value,
    # skip it
    # then map to the word of the note
    filtered_words = [
        anki.get_note_field_value(note, "Word")
        for note in notes
        if anki.has_note_field_value(note, "Word")
    ]

    # # Check if the word is in failed_words
    # if cache.is_failed_word(word) and not cache.can_reattempt(word):
    #     logging.info(f"Skipping word '{word}'.")
    #     continue  # Skip this word
    can_attempt_words = [
        word
        for word in filtered_words
        if
        # it doesn't have any pronunciations and it doesn't have any failues
        ((not cache.has_pronunciations(word)) and (not cache.is_failed_word(word)))
        # or it has failed, but we can reattempt
        or (cache.is_failed_word(word) and cache.can_reattempt(word))
    ]

    # Prepare to update notes

    try:
        for word in can_attempt_words:

            ### Check request limit
            ### BAIL COMPLETELY
            if cache.is_request_limit():
                logging.warning(f"Stopping.")
                break

            ###
            ### FETCH PRONUNCIATIONS
            ###

            logging.info(f"Fetching and storing pronunciations for word: '{word}'")
            pronunciations = forvo.fetch_and_store_pronunciations(word)

            if pronunciations == "RATE_LIMIT_REACHED":
                logging.warning("Daily request limit has been reached.")
                logging.warning('Stopping further requests."')
                # Save the cache before breaking
                cache.set_request_limit()
                break  # Stop processing further words

            ### FAILURE to fetch specific pronunciation
            if pronunciations is None:
                # Indicate failure to fetch pronunciations
                cache.increment_fetch_failure(
                    word, "Failed to fetch pronunciations due to an error."
                )
                logging.warning(
                    f"Failed to fetch pronunciations for '{word}'. Marked for retry."
                )

            ### NO EXISTING specific pronunciation
            elif not pronunciations:
                # No pronunciations found
                cache.increment_fetch_failure(word, "No pronunciations found.")
                logging.info(f"No pronunciations found for '{word}'. Marked for retry.")

            ### SUCCESSFULLY fetched pronunciation
            else:
                # Successfully fetched pronunciations
                cache.setdefault("pronunciations", {})[word] = pronunciations
                anki.write_to_buffer(word, pronunciations)

                # Remove from failed_words if present
                cache.set_unfailed(word)

                logging.info(f"Successfully fetched pronunciations for '{word}'.")

            # Increment request count if an API request was made
            cache.increment_request_count()

            # Update 'last_attempt' regardless of success or failure
            cache.set_last_attempt(word)

            # Save the updated cache after processing each word
            cache.save_cache()
            logging.info(f"Cache saved after processing word: '{word}'.")

            # To respect API rate limits, sleep if necessary
            time.sleep(1)  # Adjust based on Forvo's rate limits

    except KeyboardInterrupt:
        logging.warning("Process interrupted by user. Saving cache before exiting.")

    finally:
        # Save the cache one last time before exiting
        # save_cache(cache)
        cache.save_cache()
        logging.info("Final cache has been updated and saved.")

        # flush Anki buffer
        anki.flush_buffer()

    # Step 4: Update Anki with new pronunciations using updateNoteFields
    anki.flush_buffer()

    # Optional: Log summary of failed words
    cache.log_failed_words()


if __name__ == "__main__":
    main()
