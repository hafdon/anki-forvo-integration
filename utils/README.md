# README

## Pronunciation Updater Utility

This script updates the pronunciation field for Anki cards tagged with "preposition" using cached audio files from Forvo. It retrieves cached pronunciations from `cache.json` and applies them to the relevant cards in Anki.

#### Features

- Fetches a list of pronunciations and their associated audio files from the cache.
- Queries Anki for all cards tagged with "preposition".
- Updates the "ForvoPronunciations" field in Anki if it is empty or missing, linking it with the pronunciation data found in the cache.

#### How it works

1. The script uses the `CacheManager` to retrieve cached pronunciation data from a specified file (`cache.json`).
2. It retrieves all Anki cards tagged as "preposition" via the `AnkiNoteManager`.
3. For each card, if there is a corresponding pronunciation in the cache, it updates the "ForvoPronunciations" field of the note with the list of pronunciations.

#### Requirements

- A cache file (`cache.json`) that stores pronunciations with corresponding words.
- Anki Connect URL properly configured in the `config` file.

#### Usage

Run the script:

```bash
python pronunciation_updater.py
```

## Find Untried Words (file)
