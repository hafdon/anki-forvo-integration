import requests, json

ANKI_CONNECT_URL = 'http://localhost:8765'

def invoke(action, params=None):
    return requests.post(ANKI_CONNECT_URL, json={
        'action': action,
        'version': 6,
        'params': params
    }).json()

response = invoke('deckNames')
print(response)


### Retrieve cards in a deck:
# deck_name = 'nouns'
# query = f'deck:"{deck_name}"'
# response = invoke('findCards', {'query': query})
# print(response)

### Retrieve notes for specific cards
# card_ids = [123456789]  # Replace with actual card IDs
# params = {'cards': card_ids}
# response = invoke('cardsInfo', params)
# print(response)

### Retrieve notes information
# note_ids = [987654321]  # Replace with actual note IDs from previous step
# response = invoke('notesInfo', {'notes': note_ids})
# print(response)

# Expected Output:
#
# deckNames: A list of deck names.
# findCards: A list of card IDs within the specified deck.
# cardsInfo: Detailed information about each card, including the associated note ID.
# notesInfo: Detailed information about each note.