# Forvo Pronunciation Fetcher for Anki

A Python script that fetches pronunciations from the Forvo API, caches results to prevent redundant requests, and updates your Anki flashcards seamlessly. Designed with robust error handling to manage API rate limits and ensure data integrity.

## 🚀 Features

- **Fetch Pronunciations:** Retrieves pronunciation audio files from Forvo for words in your Anki deck.
- **Caching Mechanism:** Saves fetched data to `cache.json` to minimize API calls and handle interruptions gracefully.
- **Error Handling:** Detects and manages API rate limits, marking failed words for future retries.
- **Automated Updates:** Integrates with Anki using AnkiConnect to update flashcards with the fetched pronunciations.
- **Logging:** Maintains detailed logs (`fetch_forvo_pronunciations.log`) for monitoring and debugging.

## 🛠️ Requirements

- Python 3.7 or higher
- [AnkiConnect](https://ankiweb.net/shared/info/2055492159) Anki add-on installed and running
- Forvo API Key
  - Forvo account url: https://api.forvo.com/account/

## 📦 Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/hafdon/anki-forvo-integration.git
   cd anki-forvo-integration
   ```

2. **Create a Virtual Environment (Optional but Recommended):**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## 🔧 Configuration

1. **Environment Variables:**

   Create a `.env` file in the project root directory and populate it with the following variables:

   ```env
   ANKI_CONNECT_URL=http://localhost:8765
   FORVO_API_KEY=your_forvo_api_key
   FORVO_LANGUAGE=en  # Adjust based on your needs
   CACHE_FILE=cache.json
   DAILY_REQUEST_LIMIT=500  # Adjust according to Forvo's rate limits
   ```

   - **ANKI_CONNECT_URL:** URL where AnkiConnect is running (default is `http://localhost:8765`).
   - **FORVO_API_KEY:** Your personal Forvo API key.
   - **FORVO_LANGUAGE:** Language code for pronunciations (e.g., `en` for English).
   - **CACHE_FILE:** Path to the cache file (default is `cache.json`).
   - **DAILY_REQUEST_LIMIT:** Maximum number of API requests per day.

2. **Ensure AnkiConnect is Installed and Running:**

   - Install the [AnkiConnect](https://ankiweb.net/shared/info/2055492159) add-on in Anki.
   - Start Anki to ensure AnkiConnect is active.

## 🎬 Usage

Run the script using Python. `usage: main.py [-h] [--query QUERY]` You can run the script in various ways:

### Using Command-Line Arguments

```bash
python main.py --query 'deck:"Spanish Vocabulary" tag:verb is:due'
```

### Using Environment Variables

You can set the ANKI_SEARCH_QUERY environment variable to define a default query without needing to pass it every time:

```bash
export ANKI_SEARCH_QUERY='deck:"Spanish Vocabulary" tag:verb is:due'
python main.py
```

### Combining Both

Command-line arguments will override environment variables if both are provided.

### Example Usage

To run the script with a custom retry period of 45 days:

```bash
python main.py --query 'deck:"English Vocabulary"' --retry_after_days 45
```

If you prefer to keep the default of 30 days, you can omit the `--retry_after_days` argument:

```bash
python main.py --query 'deck:"English Vocabulary"'
```

### What It Does:

1. **Loads Cache:** Reads from `cache.json` to avoid re-fetching pronunciations.
2. **Resets Daily Limits:** Checks if a new day has started to reset the request count.
3. **Fetches Pronunciations:** Retrieves pronunciations for words in the specified Anki deck.
4. **Updates Anki:** Adds the fetched pronunciations to your Anki flashcards.
5. **Handles Errors:** Logs and marks words that failed to fetch for future retries.
6. **Saves Progress:** Continuously updates `cache.json` to preserve progress.

## 📄 Logging

All activities and errors are logged in `fetch_forvo_pronunciations.log`. Review this file to monitor the script's operations and troubleshoot issues.

## 💾 Caching

The script uses `cache.json` to store fetched pronunciations and track failed attempts. This ensures that progress is saved and the script can resume seamlessly after interruptions.

## 📝 Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## 📜 License

This project is licensed under the [MIT License](LICENSE).
