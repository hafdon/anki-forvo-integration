### Test Forvo API Separately:



import requests

FORVO_API_KEY = 'YOUR_FORVO_API_KEY'
FORVO_LANGUAGE = 'en'
word = 'example'
encoded_word = requests.utils.quote(word)
url = f'https://apifree.forvo.com/key/{FORVO_API_KEY}/format/json/action/word-pronunciations/word/{encoded_word}/language/{FORVO_LANGUAGE}'
response = requests.get(url)
print(response.json())

# Expected Output:
#
# A JSON object containing pronunciation data, including pathmp3 URLs.