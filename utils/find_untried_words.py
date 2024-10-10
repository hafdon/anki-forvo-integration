from anki.anki_note_card_manager import AnkiNoteManager
from cache.cache_manager import CacheManager
from config.config import ANKI_CONNECT_URL, CACHE_FILE
from config.logger import logger


def main():

    print("starting")

    try:
        # Initialize maangers
        anki_manager = AnkiNoteManager(ANKI_CONNECT_URL)
        cache_manager = CacheManager(CACHE_FILE, 500, 30)

        # create unique list of words on notecards
        notes = anki_manager.notes_from_query("-tag:preposition")
        words = [
            note["fields"]["Word"]["value"]
            for note in notes
            if note.get("fields", {}).get("Word", {}.get("value"))
        ]
        words = list(set(words))

        # Filter by whether or not we've attempted to fetch them
        untried = [word for word in words if cache_manager.untried(word)]

        logger.info(f"len(words): {len(words)}")
        logger.info(f"len(untried): {len(untried)}")
        logger.info(f"difference: {len(words) - len(untried)}")

    except:
        logger.exception("Exception")


if __name__ == "__main__":
    main()
