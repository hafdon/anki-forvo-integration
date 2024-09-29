import json
import os
import time
from datetime import datetime

import requests
# import logging

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
ANKI_CONNECT_URL = os.getenv('ANKI_CONNECT_URL')
FORVO_API_KEY = os.getenv('FORVO_API_KEY')  # Replace with your actual Forvo API key
FORVO_LANGUAGE = os.getenv('FORVO_LANGUAGE')  # Adjust based on your needs

DECK_NAME = 'nouns'  # Replace with your deck name
MODEL_NAME = 'Basic'  # Replace with your model name
FIELD_NAME = 'ForvoPronunciations'  # New field to store Forvo URLs

CACHE_FILE = os.getenv('CACHE_FILE')  # File to store cached data

# Forvo API limit
# DAILY_REQUEST_LIMIT = os.getenv('DAILY_REQUEST_LIMIT')
DAILY_REQUEST_LIMIT = 500     # Adjust based on Forvo's rate limits


# Function to make requests to AnkiConnect
def invoke(action, params=None):
    try:
        response = requests.post(ANKI_CONNECT_URL, json={
            'action': action,
            'version': 6,
            'params': params
        })
        response.raise_for_status()
        result = response.json()
        return result
    except requests.exceptions.RequestException as e:
        print(f"HTTP Request failed: {e}")
        return {"error": str(e)}


# Load cache from file
def load_cache():
    if not os.path.exists(CACHE_FILE):
        # Initialize cache structure
        cache = {
            'pronunciations': {},  # word: [list of URLs]
            'request_count': 0,  # Number of API requests made today
            'last_reset': datetime.today().strftime('%Y-%m-%d')  # Last reset date
        }
        save_cache(cache)
        return cache
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


# Save cache to file
def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=4)


# Reset request count if it's a new day
def reset_request_count_if_new_day(cache):
    today = datetime.today().strftime('%Y-%m-%d')
    if cache['last_reset'] != today:
        cache['request_count'] = 0
        cache['last_reset'] = today
        print("Daily request count has been reset.")
    return cache


# Step 1: Retrieve all cards from the specified deck
def get_deck_cards(deck_name):
    query = f'deck:"{deck_name}"'
    params = {
        'query': query
    }
    response = invoke('findCards', params)
    if 'error' in response and response['error']:
        print(f"Error finding cards: {response['error']}")
        return []
    card_ids = response.get('result', [])
    print(f"Found {len(card_ids)} cards in deck '{deck_name}'.")
    return card_ids


# Step 2: Get notes by card IDs (Corrected Function)
def get_notes(card_ids):
    # First, get card information to retrieve note IDs
    params = {
        'cards': card_ids
    }
    response = invoke('cardsInfo', params)
    if 'error' in response and response['error']:
        print(f"Error retrieving cards info: {response['error']}")
        return []

    card_info = response.get('result', [])

    # Extract unique note IDs from card information
    note_ids = [card['note'] for card in card_info if 'note' in card]
    unique_note_ids = list(set(note_ids))

    if not unique_note_ids:
        print("No note IDs found for the given cards.")
        return []

    # Now, retrieve note information using note IDs
    params = {
        'notes': unique_note_ids
    }
    response = invoke('notesInfo', params)
    if 'error' in response and response['error']:
        print(f"Error retrieving notes: {response['error']}")
        return []

    return response.get('result', [])


# Step 3: Fetch pronunciation URLs from Forvo
def fetch_forvo_pronunciations(word):
    # Encode the word for URL
    encoded_word = requests.utils.quote(word)
    url = f'https://apifree.forvo.com/key/{FORVO_API_KEY}/format/json/action/word-pronunciations/word/{encoded_word}/language/{FORVO_LANGUAGE}'

    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error fetching Forvo data for '{word}': Status {response.status_code}")
            return []

        data = response.json()
        pronunciations = []

        if 'items' in data:
            for item in data['items']:
                if item.get('pathmp3'):
                    # Construct the full URL if necessary
                    mp3_path = item['pathmp3']
                    if not mp3_path.startswith('/'):
                        mp3_path = '/' + mp3_path
                    mp3_url = f"https://apifree.forvo.com{mp3_path}"
                    pronunciations.append(mp3_url)

        return pronunciations
    except Exception as e:
        print(f"Exception occurred while fetching Forvo data for '{word}': {e}")
        return []


# Step 4: Update Anki cards with Forvo pronunciations using updateNoteFields
def update_anki_notes(notes, field_name, pronunciations_dict):
    if not notes:
        return

    notes_to_update = []
    for note in notes:
        word = note['fields'].get('Word', {}).get('value', '').strip()
        if not word:
            continue  # Skip if no word found

        pronunciations = pronunciations_dict.get(word, [])
        if pronunciations:
            # Create HTML audio players for each pronunciation
            audio_html = ''.join([f'<audio controls src="{url}"></audio><br>' for url in pronunciations])

            # Prepare the note object for updateNoteFields
            note_update = {
                "id": note['noteId'],  # Ensure 'id' is correct
                "fields": {
                    field_name: audio_html
                }
            }
            notes_to_update.append(note_update)

    if not notes_to_update:
        print("No new pronunciations to update.")
        return

    # Send update to Anki
    params = {
        "note": None  # Placeholder
    }

    # Prepare a list of update requests
    for note_update in notes_to_update:
        params = {
            "note": {
                "id": note_update["id"],
                "fields": note_update["fields"]
            }
        }
        response = invoke('updateNoteFields', params)
        if 'error' in response and response['error']:
            print(f"Error updating note ID {note_update['id']}: {response['error']}")
        else:
            print(f"Successfully updated note ID {note_update['id']} with Forvo pronunciations.")


def main():
    # Load cache
    cache = load_cache()

    # Reset request count if a new day
    cache = reset_request_count_if_new_day(cache)

    # Step 1: Get all card IDs in the deck
    card_ids = get_deck_cards(DECK_NAME)

    if not card_ids:
        print("No cards found. Exiting.")
        return

    # Step 2: Get note information
    notes = get_notes(card_ids)

    # Prepare to update notes
    pronunciations_dict = {}
    notes_to_update = []

    for note in notes:
        word = note['fields'].get('Word', {}).get('value', '').strip()
        if not word:
            continue  # Skip if no word found

        # Check if the word is already in cache
        if word in cache['pronunciations']:
            pronunciations = cache['pronunciations'][word]
            if pronunciations:
                pronunciations_dict[word] = pronunciations
            continue  # Skip to next word

        # Check if daily limit is reached
        if cache['request_count'] >= DAILY_REQUEST_LIMIT:
            print(f"Daily request limit of {DAILY_REQUEST_LIMIT} reached. Stopping.")
            break

        print(f"Fetching pronunciations for word: '{word}'")
        pronunciations = fetch_forvo_pronunciations(word)

        # Update cache
        cache['pronunciations'][word] = pronunciations
        if pronunciations:
            pronunciations_dict[word] = pronunciations

        # Increment request count if an API request was made
        cache['request_count'] += 1

        # Prepare the updated note
        notes_to_update.append({
            "id": note['noteId'],  # Ensure 'id' is used
            "fields": {
                FIELD_NAME: ''.join([f'<audio controls src="{url}"></audio><br>' for url in pronunciations])
            }
        })

        # To respect API rate limits, sleep if necessary
        time.sleep(1)  # Adjust based on Forvo's rate limits

    # Step 4: Update Anki with new pronunciations using updateNoteFields
    if notes_to_update:
        update_anki_notes(notes, FIELD_NAME, pronunciations_dict)
    else:
        print("No new pronunciations to update.")

    # Save the updated cache
    save_cache(cache)
    print("Cache has been updated and saved.")


if __name__ == "__main__":
    main()
