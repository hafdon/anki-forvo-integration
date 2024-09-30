import os
import re
import requests
import json
from collections import defaultdict

# Configuration
ANKI_CONNECT_URL = "http://localhost:8765"
MEDIA_DIR = os.getenv("MEDIA_DIR")
AUDIO_FILE_PATTERN = r"^(.+?)_random(?:_\d+)?\.mp3$"
NOTE_TYPE = "Basic"
SEARCH_FIELD = "Word"
TARGET_FIELD = "ForvoPronunciations"


def invoke(action, params=None):
    """Helper function to call AnkiConnect API."""
    return requests.post(
        ANKI_CONNECT_URL,
        json.dumps({"action": action, "version": 6, "params": params or {}}),
    ).json()


def get_media_files():
    """Retrieve all relevant audio files from the media directory."""
    files = os.listdir(MEDIA_DIR)
    audio_files = [f for f in files if re.match(AUDIO_FILE_PATTERN, f)]
    return audio_files


def extract_word(filename):
    """Extract the word from the filename using regex."""
    match = re.match(AUDIO_FILE_PATTERN, filename)
    if match:
        return match.group(1)
    return None


def get_notes_by_word(word):
    """Retrieve note IDs that have the specified word in the SEARCH_FIELD."""
    query = f'"{word}"'
    response = invoke("findNotes", {"query": f'{SEARCH_FIELD}:"{word}"'})
    if response.get("error"):
        print(f"Error finding notes for word '{word}': {response['error']}")
        return []
    return response.get("result", [])


def get_note_fields(note_ids):
    """Retrieve the fields of the given notes."""
    response = invoke("notesInfo", {"notes": note_ids})
    if response.get("error"):
        print(f"Error retrieving note info: {response['error']}")
        return []
    return response.get("result", [])


def update_note_field(note_id, field_name, new_content):
    """Update a specific field of a note."""
    params = {"note": {"id": note_id, "fields": {field_name: new_content}}}
    response = invoke("updateNoteFields", params)
    if response.get("error"):
        print(f"Error updating note {note_id}: {response['error']}")


def main():
    audio_files = get_media_files()
    if not audio_files:
        print("No audio files found matching the pattern.")
        return

    # Map words to their audio files
    word_to_audios = defaultdict(list)
    for audio in audio_files:
        word = extract_word(audio)
        if word:
            word_to_audios[word].append(audio)
        else:
            print(
                f"Filename '{audio}' does not match the expected pattern and will be skipped."
            )

    # Iterate over each word and update corresponding notes
    for word, audios in word_to_audios.items():
        note_ids = get_notes_by_word(word)
        if not note_ids:
            print(f"No notes found for word '{word}'.")
            continue

        # Prepare the audio references
        audio_refs = "".join([f"[sound:{audio}] " for audio in audios]).strip()

        # Update each note's ForvoPronunciation field
        notes_info = get_note_fields(note_ids)
        for note in notes_info:
            current_content = note["fields"].get(TARGET_FIELD, {}).get("value", "")
            updated_content = (
                current_content + " " + audio_refs if current_content else audio_refs
            )
            updated_content = updated_content.strip()
            update_note_field(note["noteId"], TARGET_FIELD, updated_content)
            print(
                f"Updated note ID {note['noteId']} with audio files: {', '.join(audios)}"
            )

    print("All applicable notes have been updated.")


if __name__ == "__main__":
    main()
