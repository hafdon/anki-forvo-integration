import requests
import json
import time
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configuration
ANKI_CONNECT_URL = os.getenv('ANKI_CONNECT_URL')
FORVO_API_KEY = os.getenv('FORVO_API_KEY')  # Replace with your actual Forvo API key
FORVO_LANGUAGE = os.getenv('FORVO_LANGUAGE')  # Adjust based on your needs

DECK_NAME = 'nouns'  # Replace with your deck name
MODEL_NAME = 'Basic'  # Replace with your model name
FIELD_NAME = 'ForvoPronunciations'  # New field to store Forvo URLs


# Function to make requests to AnkiConnect
def invoke(action, params=None):
    return requests.post(ANKI_CONNECT_URL, json={
        'action': action,
        'version': 6,
        'params': params
    }).json()


# Step 1: Retrieve all cards from the specified deck
def get_deck_cards(deck_name):
    params = {
        'deck': deck_name
    }
    return invoke('findCards', params)['result']


# Step 2: Get notes by card IDs
def get_notes(card_ids):
    params = {
        'cards': card_ids
    }
    return invoke('notesInfo', params)['result']


# Step 3: Fetch pronunciation URLs from Forvo
def fetch_forvo_pronunciations(word):
    url = 'https://apifree.forvo.com/key/{}/format/json/action/word-pronunciations/word/{}'.format(
        FORVO_API_KEY, requests.utils.quote(word)
    )
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching Forvo data for {word}: Status {response.status_code}")
        return []

    data = response.json()
    pronunciations = []

    if 'items' in data:
        for item in data['items']:
            if item.get('pathmp3'):
                pronunciations.append(item['pathmp3'])

    return pronunciations


# Step 4: Update Anki cards with Forvo pronunciations
def update_anki_notes(notes, field_name, pronunciations):
    for note in notes:
        # Create HTML audio players for each pronunciation
        audio_html = ''.join([f'<audio controls src="{url}"></audio><br>' for url in pronunciations])
        # Update the field
        note['fields'][field_name] = audio_html
    # Send update to Anki
    invoke('updateNotes', {'notes': notes})


def main():
    # Step 1: Get all card IDs in the deck
    card_ids = get_deck_cards(DECK_NAME)
    print(f"Found {len(card_ids)} cards in deck '{DECK_NAME}'.")

    # Step 2: Get note information
    notes = get_notes(card_ids)

    # Prepare to update notes
    notes_to_update = []

    for note in notes:
        word = note['fields'].get('Word', {}).get('value', '').strip()
        if not word:
            continue  # Skip if no word found

        print(f"Processing word: {word}")
        pronunciations = fetch_forvo_pronunciations(word)
        if pronunciations:
            # Prepare the updated note
            notes_to_update.append({
                'id': note['noteId'],
                'fields': {
                    FIELD_NAME: ''.join(
                        [f'<audio controls src="https://apifree.forvo.com/{url}"></audio><br>' for url in
                         pronunciations])
                }
            })
        else:
            print(f"No pronunciations found for {word}.")

        # To respect API rate limits
        time.sleep(1)  # Adjust based on Forvo's rate limits

    # Step 4: Update Anki with new pronunciations
    if notes_to_update:
        update_anki_notes(notes_to_update, FIELD_NAME, pronunciations=None)  # pronunciations handled in 'fields'
        print(f"Updated {len(notes_to_update)} notes with Forvo pronunciations.")
    else:
        print("No pronunciations to update.")


if __name__ == "__main__":
    main()
