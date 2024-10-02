import argparse

from anki.anki_note_card_manager import AnkiNoteCardManager
from anki.anki_pronunciations_manager import AnkiPronunciationsManager
from anki.anki_file_manager import AnkiFileManager
from backup_manager import BackupManager
from cache.cache_manager import CacheManager
from config.config import ANKI_CONNECT_URL, RETRY_AFTER_DAYS
from config.logger import logger

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
    # backup = BackupManager()

    # backup.limit_backups()
    # backup.backup_cache()

    # Parse command-line arguments for the search query and retry configuration
    search_query, retry_after_days = parse_local_args()
    print(search_query, retry_after_days)

    # cache = CacheManager(CACHE_FILE, DAILY_REQUEST_LIMIT, retry_after_days)

    # anki_files = AnkiFileManager()

    # print(anki_files.get_media_files())

    # files = anki_files.get_media_files()

    # for filename in files:
    #     word = anki_files.extract_word(filename)
    #     print(f"{word}")

    anki_pronunciations = AnkiPronunciationsManager()

    print(anki_pronunciations.get_buffer())

    print("print(anki_pronunciations.get_buffer())")
    anki_pronunciations.write_to_buffer("noob", ["[sound:noob_random.mp3]"])
    print('anki_pronunciations.write_to_buffer("noob", ["[sound:noob_random.mp3]"])')
    print("print(anki_pronunciations.get_buffer())")
    print(anki_pronunciations.get_buffer())

    # Make sure flush_buffer() is implemented before using it
    try:
        anki_pronunciations.flush_buffer()
    except NotImplementedError as e:
        print(f"{e}")
    else:
        print("anki_pronunciations.flush_buffer() is implemented")

    anki_note_card_manager = AnkiNoteCardManager(ANKI_CONNECT_URL)
    # anki_note_card_manager.cards_from_query(search_query)
    notes = anki_note_card_manager.notes_from_query(search_query)

    # filtered_notes = [
    #     note
    #     for note in notes
    #     if anki_note_card_manager.has_note_field_value(note, "Word")
    # ]
    # print(f"filtered_notes: { len(filtered_notes)}")

    print(notes[0])

    # print("Check log file for details.")

    note_field = anki_note_card_manager.get_note_fields([notes[0]["noteId"]])

    note_id = notes[0]["noteId"]
    field_name = "Word"
    new_content = "aoine1"

    anki_note_card_manager.update_note_field(note_id, field_name, new_content)

    updated_note_id = anki_note_card_manager.get_note_ids_by_word("aoine1")
    print("updated_note_id", updated_note_id)

    note_word = anki_note_card_manager.get_note_fields(updated_note_id)


if __name__ == "__main__":
    main()
