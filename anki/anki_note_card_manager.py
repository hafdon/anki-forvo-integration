from anki.anki_invoker import AnkiInvoker
from config.logger import logger


class AnkiNoteManager:
    def __init__(self, connect_url) -> None:
        self.invoker = AnkiInvoker(connect_url)
        pass

    def note_ids_from_query(self, search_query):
        # Can't be a space in between Word:word
        params = {"query": search_query}
        response = self.invoker.invoke("findNotes", params)
        if "error" in response and response["error"]:
            logger.error(
                f"Error finding notes with query '{search_query}': {response['error']}"
            )
            return []
        note_ids = response.get("result", [])
        logger.info(f"Found {len(note_ids)} notes with query'{search_query}")
        return note_ids

    def notes_from_query(self, search_query):
        # # Can't be a space in between Word:word
        # params = {"query": search_query}
        # response = self.invoker.invoke("findNotes", params)
        # if "error" in response and response["error"]:
        #     logger.error(
        #         f"Error finding notes with query '{search_query}': {response['error']}"
        #     )
        #     return []
        # note_ids = response.get("result", [])

        note_ids = self.note_ids_from_query(search_query)

        logger.info(f"Found {len(note_ids)} notes with query'{search_query}")

        return self.notes_from_note_ids(note_ids)

    def notes_from_note_ids(self, note_ids):

        # Step 2: Retrieve full note information using notesInfo
        notes_info_params = {"notes": note_ids}
        notes_info_response = self.invoker.invoke("notesInfo", notes_info_params)

        # Error handling for notesInfo
        if "error" in notes_info_response and notes_info_response["error"]:
            logger.error(notes_info_response["error"])
            return []

        notes = notes_info_response.get("result", [])
        logger.info(f"Retrieved detailed information for {len(notes)} notes.")

        return notes

    def update_note_field(self, note_id, field_name, new_content):
        """Update a specific field of a note."""
        params = {"note": {"id": note_id, "fields": {field_name: new_content}}}
        response = self.invoker.invoke("updateNoteFields", params)
        if response.get("error"):
            print(f"Error updating note {note_id}: {response['error']}")

    # def notes_from_card_ids(self, card_ids):
    #     if not card_ids:
    #         logger.warning("No card IDs provided to get_notes.")
    #         return []
    #     # First, get card information to retrieve note IDs
    #     params = {"cards": card_ids}
    #     response = self.invoker.invoke("cardsInfo", params)
    #     if "error" in response and response["error"]:
    #         logger.error(f"Error retrieving cards info: {response['error']}")
    #         return []

    #     card_info = response.get("result", [])
    #     if not card_info:
    #         logger.warning("No card information retrieved.")
    #         return []

    #     # Extract unique note IDs from card information
    #     note_ids = [card["note"] for card in card_info if "note" in card]
    #     unique_note_ids = list(set(note_ids))

    #     if not unique_note_ids:
    #         logger.warning("No unique note IDs found for the given cards.")
    #         return []

    #     # Now, retrieve note information using note IDs
    #     params = {"notes": unique_note_ids}
    #     response = self.invoker.invoke("notesInfo", params)
    #     if "error" in response and response["error"]:
    #         logger.error(f"Error retrieving notes: {response['error']}")
    #         return []

    #     notes = response.get("result", [])
    #     logger.info(f"Retrieved information for {len(notes)} notes.")
    #     return notes

    # def get_note_field_value(self, note, field_label="Word"):
    #     return note["fields"].get(field_label, {}).get("value", "").strip()

    # def has_note_field_value(self, note, field_label="Word"):
    #     if self.get_note_field_value(note, field_label):
    #         return True
    #     return False

    # def get_note_ids_by_word(self, word):
    #     """Retrieve note IDs that have the specified word in the SEARCH_FIELD."""
    #     query = f'"{word}"'
    #     response = self.invoker.invoke(
    #         "findNotes", {"query": f'{SEARCH_FIELD}:"{word}"'}
    #     )
    #     if response.get("error"):
    #         print(f"Error finding notes for word '{word}': {response['error']}")
    #         return []
    #     return response.get("result", [])

    # def get_note_fields(self, note_ids):
    #     """Retrieve the fields of the given notes.
    #     These appear to be the same values as if you just look at notes[0], etc.
    #     """
    #     response = self.invoker.invoke("notesInfo", {"notes": note_ids})
    #     if response.get("error"):
    #         print(f"Error retrieving note info: {response['error']}")
    #         return []
    #     return response.get("result", [])

    # Step 1: Retrieve all cards based on a search query
    # def cards_from_query(self, search_query):
    #     params = {"query": search_query}
    #     response = self.invoker.invoke("findCards", params)
    #     if "error" in response and response["error"]:
    #         logger.error(
    #             f"Error finding cards with query '{search_query}': {response['error']}"
    #         )
    #         return []
    #     card_ids = response.get("result", [])
    #     logger.info(f"Found {len(card_ids)} cards with query '{search_query}'.")
    #     return card_ids
