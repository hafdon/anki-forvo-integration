import os
import time
import argparse
from datetime import datetime, timedelta

import logging

from anki_helper import get_cards, get_notes, update_anki_notes
from cache.cache_manager import CacheManager
from cache_helper import load_cache, reset_request_count_if_new_day, save_cache
from forvo_helper import fetch_and_store_pronunciations

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

# Setup logging
logging.basicConfig(
    filename="fetch_forvo_pronunciations.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


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
        "--retry_after_days",
        type=int,
        default=30,
        help="Number of days to wait before retrying a failed word (default: 30)",
    )
    args = parser.parse_args()
    search_query = args.query
    retry_after_days = args.retry_after_days
    return search_query, retry_after_days


def notes_from_query(cards):

    # Step 1: Get all card IDs based on the search query
    card_ids = get_cards(search_query)

    if not card_ids:
        logging.info("No cards found.")
        return False

    # Step 2: Get note information
    notes = get_notes(card_ids)

    if not notes:
        logging.info("No notes found.")
        return False

    return notes


def main():
    # Parse command-line arguments for the search query and retry configuration
    search_query, retry_after_days = parse_local_args()

    cache = CacheManager(CACHE_FILE)
    # Load cache
    cache.load_cache(CACHE_FILE)

    # Reset request count if a new day
    cache.reset_request_count_if_new_day()

    notes = notes_from_query(search_query)
    if not notes:
        logging.info("No notes found. Exiting.")
        return

    # Prepare to update notes
    pronunciations_dict = {}

    try:
        for note in notes:

            # Check if daily limit is reached
            # Don't bother checking if so
            if cache.is_request_limit():
                logging.warning(f"Stopping.")
                break

            # Get the value of the 'Word' field.
            word = note["fields"].get("Word", {}).get("value", "").strip()
            if not word:
                logging.warning("Encountered a note without a 'Word' field. Skipping.")
                continue  # Skip if no word found

            # Check if the word is already in cache["pronunciations"]
            if word in cache.get("pronunciations", {}):
                # pronunciations = the value of key "word" (an array of pronunciations)
                pronunciations = cache["pronunciations"][word]
                # if these pronunciations exist, add them to the
                # dict structure. This dict structure is later used to update notes
                if pronunciations:
                    pronunciations_dict[word] = pronunciations
                continue  # Skip to next word

            # Check if the word is in failed_words
            # failed_words = cache.get_failed_words()
            if cache.is_failed_word(word):
                # last_attempt_str = failed_words[word].get("last_attempt")
                # last_attempt_str = cache.get_last_attempt_str(word)
                # if last_attempt_str:
                # try:
                # last_attempt = datetime.strptime(
                #     last_attempt_str, "%Y-%m-%d %H:%M:%S"
                # )
                time_since_last_attempt = cache.get_time_since_last_attempt(word)
                if time_since_last_attempt < timedelta(days=retry_after_days):
                    logging.info(
                        f"Skipping word '{word}' as last attempt was {time_since_last_attempt.days} days ago."
                    )
                    continue  # Skip this word
                else:
                    logging.info(f"Retrying pronunciation fetch for word: '{word}'")
                    # except ValueError:
                    #     logging.warning(
                    #         f"Invalid date format for word '{word}'. Proceeding to retry."
                    #     )
                # else:
                #     logging.info(
                #         f"No 'last_attempt' found for word '{word}'. Proceeding to retry."
                #     )
            else:
                logging.info(f"Fetching pronunciations for new word: '{word}'")

            logging.info(f"Fetching and storing pronunciations for word: '{word}'")
            pronunciations = fetch_and_store_pronunciations(word)

            if pronunciations == "RATE_LIMIT_REACHED":
                logging.warning("Daily request limit has been reached.")
                logging.warning('Stopping further requests."')
                # Save the cache before breaking
                cache.set_request_limit()
                break  # Stop processing further words

            ###
            ###
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
            else:
                # Successfully fetched pronunciations
                cache.setdefault("pronunciations", {})[word] = pronunciations
                pronunciations_dict[word] = pronunciations
                # Remove from failed_words if present
                if "failed_words" in cache and word in cache["failed_words"]:
                    del cache["failed_words"][word]
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
        save_cache(cache)
        logging.info("Final cache has been updated and saved.")

    # Step 4: Update Anki with new pronunciations using updateNoteFields
    if pronunciations_dict:
        update_anki_notes(notes, FIELD_NAME, pronunciations_dict)
    else:
        logging.info("No new pronunciations to update.")

    # Optional: Log summary of failed words
    cache.log_failed_words()


if __name__ == "__main__":
    main()
