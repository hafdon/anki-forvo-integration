import json
import os
import time
import argparse
from datetime import datetime

import requests
import logging

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


# Function to make requests to AnkiConnect
def invoke(action, params=None):
    try:
        response = requests.post(
            ANKI_CONNECT_URL, json={"action": action, "version": 6, "params": params}
        )
        response.raise_for_status()
        result = response.json()
        return result
    except requests.exceptions.RequestException as e:
        logging.error(f"HTTP Request failed for action '{action}': {e}")
        return {"error": str(e)}


# Load cache from file
def load_cache():
    if not os.path.exists(CACHE_FILE):
        # Initialize cache structure
        cache = {
            "pronunciations": {},  # word: [list of filenames]
            "failed_words": {},  # word: {"error": "Error message", "attempts": 0}
            "request_count": 0,  # Number of API requests made today
            "last_reset": datetime.today().strftime("%Y-%m-%d"),  # Last reset date
        }
        save_cache(cache)
        return cache
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# Save cache to file (atomic write)
def save_cache(cache):
    temp_file = CACHE_FILE + ".tmp"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=4)
        os.replace(temp_file, CACHE_FILE)
    except Exception as e:
        logging.error(f"Failed to save cache to '{CACHE_FILE}': {e}")


# Reset request count if it's a new day
def reset_request_count_if_new_day(cache):
    today = datetime.today().strftime("%Y-%m-%d")
    if cache["last_reset"] != today:
        cache["request_count"] = 0
        cache["last_reset"] = today
        logging.info("Daily request count has been reset.")
    return cache


# Step 1: Retrieve all cards based on a search query
def get_cards(query):
    params = {"query": query}
    response = invoke("findCards", params)
    if "error" in response and response["error"]:
        logging.error(f"Error finding cards with query '{query}': {response['error']}")
        return []
    card_ids = response.get("result", [])
    logging.info(f"Found {len(card_ids)} cards with query '{query}'.")
    return card_ids


# Step 2: Get notes by card IDs
def get_notes(card_ids):
    if not card_ids:
        logging.warning("No card IDs provided to get_notes.")
        return []
    # First, get card information to retrieve note IDs
    params = {"cards": card_ids}
    response = invoke("cardsInfo", params)
    if "error" in response and response["error"]:
        logging.error(f"Error retrieving cards info: {response['error']}")
        return []

    card_info = response.get("result", [])
    if not card_info:
        logging.warning("No card information retrieved.")
        return []

    # Extract unique note IDs from card information
    note_ids = [card["note"] for card in card_info if "note" in card]
    unique_note_ids = list(set(note_ids))

    if not unique_note_ids:
        logging.warning("No unique note IDs found for the given cards.")
        return []

    # Now, retrieve note information using note IDs
    params = {"notes": unique_note_ids}
    response = invoke("notesInfo", params)
    if "error" in response and response["error"]:
        logging.error(f"Error retrieving notes: {response['error']}")
        return []

    notes = response.get("result", [])
    logging.info(f"Retrieved information for {len(notes)} notes.")
    return notes


# Function to fetch and store pronunciations from Forvo
def fetch_and_store_pronunciations(word):
    # Encode the word for URL
    encoded_word = requests.utils.quote(word)
    url = f"https://apifree.forvo.com/key/{FORVO_API_KEY}/format/json/action/word-pronunciations/word/{encoded_word}/language/{FORVO_LANGUAGE}"

    try:
        response = requests.get(url)
        if response.status_code == 429:
            # Rate limit exceeded
            logging.warning(
                f"Rate limit (429) exceeded when fetching '{word}'. Sleeping for 60 seconds."
            )
            time.sleep(60)
            response = requests.get(url)  # Retry after sleeping

        if response.status_code == 400:
            # Check if the error message indicates rate limit
            try:
                error_message = response.json()
            except ValueError:
                error_message = response.text

            if (
                isinstance(error_message, list)
                and "Limit/day reached." in error_message
            ):
                logging.warning(f"Daily request limit reached when fetching '{word}'.")
                return "RATE_LIMIT_REACHED"

        if response.status_code != 200:
            # Log the response body for debugging
            try:
                error_details = response.json()
            except ValueError:
                error_details = response.text
            logging.error(
                f"Error fetching Forvo data for '{word}': Status {response.status_code}, Response: {error_details}"
            )
            return None  # Indicate failure to fetch

        data = response.json()
        filenames = []

        if "items" in data and isinstance(data["items"], list):
            mp3_index = 1
            for item in data["items"]:
                if item.get("pathmp3"):
                    mp3_url = item["pathmp3"]

                    # Check if mp3_url is already a full URL
                    if not mp3_url.startswith("http"):
                        # If it's a relative path, prepend the base URL
                        if not mp3_url.startswith("/"):
                            mp3_url = "/" + mp3_url
                        mp3_url = f"https://apifree.forvo.com{mp3_url}"

                    # Generate a unique filename
                    dialect = item.get("dialect", "random").replace(
                        " ", "_"
                    )  # Assuming 'dialect' field exists
                    filename = f"{word}_{dialect}_{mp3_index}.mp3".replace(
                        "/", "_"
                    )  # Replace any '/' to avoid path issues
                    mp3_index += 1

                    # Store the media file in Anki
                    store_params = {"filename": filename, "url": mp3_url}
                    store_response = invoke("storeMediaFile", store_params)
                    if "error" in store_response and store_response["error"]:
                        logging.error(
                            f"Error storing media file '{filename}': {store_response['error']}"
                        )
                        continue
                    stored_filename = store_response.get("result")
                    if stored_filename:
                        filenames.append(f"[sound:{stored_filename}]")
                        logging.info(f"Stored media file '{stored_filename}'.")
                    else:
                        logging.error(f"Failed to store media file for '{word}'.")

        if not filenames:
            logging.warning(f"No pronunciations found for '{word}'.")
            return []  # Indicate no pronunciations found

        return filenames

    except Exception as e:
        logging.error(
            f"Exception occurred while fetching/storing Forvo data for '{word}': {e}"
        )
        return None  # Indicate failure to fetch


# Step 4: Update Anki notes with Forvo pronunciations using updateNoteFields
def update_anki_notes(notes, field_name, pronunciations_dict):
    if not notes:
        logging.warning("No notes provided to update_anki_notes.")
        return

    for note in notes:
        word = note["fields"].get("Word", {}).get("value", "").strip()
        if not word:
            logging.warning("Encountered a note without a 'Word' field. Skipping.")
            continue  # Skip if no word found

        pronunciations = pronunciations_dict.get(word, [])
        if pronunciations:
            # Join all [sound:...] tags with line breaks
            sounds = "<br>".join(pronunciations)

            # Prepare the note object for updateNoteFields
            note_update = {
                "id": note["noteId"],  # Ensure 'id' is correct
                "fields": {field_name: sounds},
            }

            # Invoke updateNoteFields for each note
            params = {"note": note_update}
            response = invoke("updateNoteFields", params)
            if "error" in response and response["error"]:
                logging.error(
                    f"Error updating note ID {note['noteId']}: {response['error']}"
                )
            else:
                logging.info(
                    f"Successfully updated note ID {note['noteId']} with Forvo pronunciations."
                )


def main():
    # Parse command-line arguments for the search query and retry configuration
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

    # Load cache
    cache = load_cache()

    # Reset request count if a new day
    cache = reset_request_count_if_new_day(cache)

    # Step 1: Get all card IDs based on the search query
    card_ids = get_cards(search_query)

    if not card_ids:
        logging.info("No cards found. Exiting.")
        return

    # Step 2: Get note information
    notes = get_notes(card_ids)

    # Prepare to update notes
    pronunciations_dict = {}

    try:
        for note in notes:
            # Get the value of the 'Word' field.
            word = note["fields"].get("Word", {}).get("value", "").strip()
            if not word:
                logging.warning("Encountered a note without a 'Word' field. Skipping.")
                continue  # Skip if no word found

            # Check if the word is already in cache["pronunciations"]
            if word in cache.get("pronunciations", {}):
                pronunciations = cache["pronunciations"][word]
                if pronunciations:
                    pronunciations_dict[word] = pronunciations
                continue  # Skip to next word

            # Check if the word is in failed_words
            failed_words = cache.get("failed_words", {})
            if word in failed_words:
                last_attempt_str = failed_words[word].get("last_attempt")
                if last_attempt_str:
                    try:
                        last_attempt = datetime.strptime(
                            last_attempt_str, "%Y-%m-%d %H:%M:%S"
                        )
                        time_since_last_attempt = datetime.now() - last_attempt
                        if time_since_last_attempt < timedelta(days=retry_after_days):
                            logging.info(
                                f"Skipping word '{word}' as last attempt was {time_since_last_attempt.days} days ago."
                            )
                            continue  # Skip this word
                        else:
                            logging.info(
                                f"Retrying pronunciation fetch for word: '{word}'"
                            )
                    except ValueError:
                        logging.warning(
                            f"Invalid date format for word '{word}'. Proceeding to retry."
                        )
                else:
                    logging.info(
                        f"No 'last_attempt' found for word '{word}'. Proceeding to retry."
                    )
            else:
                logging.info(f"Fetching pronunciations for new word: '{word}'")

            # Check if daily limit is reached
            if cache.get("request_count", 0) >= DAILY_REQUEST_LIMIT:
                logging.warning(
                    f"Daily request limit of {DAILY_REQUEST_LIMIT} reached. Stopping."
                )
                break

            logging.info(f"Fetching and storing pronunciations for word: '{word}'")
            pronunciations = fetch_and_store_pronunciations(word)

            if pronunciations == "RATE_LIMIT_REACHED":
                # Update request_count to the limit
                cache["request_count"] = DAILY_REQUEST_LIMIT
                logging.warning(
                    "Daily request limit has been reached. Stopping further requests."
                )
                # Save the cache before breaking
                save_cache(cache)
                break  # Stop processing further words

            if pronunciations is None:
                # Indicate failure to fetch pronunciations
                cache.setdefault("failed_words", {})[word] = {
                    "error": "Failed to fetch pronunciations due to an error.",
                    "attempts": cache.get("failed_words", {})
                    .get(word, {})
                    .get("attempts", 0)
                    + 1,
                    "last_attempt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                logging.warning(
                    f"Failed to fetch pronunciations for '{word}'. Marked for retry."
                )
            elif not pronunciations:
                # No pronunciations found
                cache.setdefault("failed_words", {})[word] = {
                    "error": "No pronunciations found.",
                    "attempts": cache.get("failed_words", {})
                    .get(word, {})
                    .get("attempts", 0)
                    + 1,
                    "last_attempt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
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
            cache["request_count"] = cache.get("request_count", 0) + 1

            # Update 'last_attempt' regardless of success or failure
            if "failed_words" in cache and word not in cache["pronunciations"]:
                cache["failed_words"][word]["last_attempt"] = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

            # Save the updated cache after processing each word
            save_cache(cache)
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
    if "failed_words" in cache and cache["failed_words"]:
        logging.info(f"Total failed words: {len(cache['failed_words'])}")
        for word, details in cache["failed_words"].items():
            logging.info(f"Word: {word}, Details: {details}")


if __name__ == "__main__":
    main()
