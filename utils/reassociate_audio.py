# get the list of pronunciations and associated audio files in cache.json
# go through "tag:preposition" in aki
# update ForvoPronunciation field if it's empty

from anki.anki_note_card_manager import AnkiNoteManager
from cache.cache_manager import CacheManager
from config.config import ANKI_CONNECT_URL, CACHE_FILE


def main():

    cache_manager = CacheManager(CACHE_FILE, 500, 30)
    anki_manager = AnkiNoteManager(ANKI_CONNECT_URL)

    pronunciations = cache_manager.get_all_pronunciations()
    prepositions = anki_manager.notes_from_query("tag:preposition")

    for prep in prepositions:

        word = anki_manager.get_note_field_value(prep)
        note_id = prep.get("noteId")

        # The notecard has associated pronunciation files
        if note_id and word and word in pronunciations:

            print("Not a problem", note_id, word, pronunciations.get(word))

            anki_manager.update_note_field(
                note_id, "ForvoPronunciations", " ".join(pronunciations[word])
            )

        else:
            print("Problem")


if __name__ == "__main__":
    main()
