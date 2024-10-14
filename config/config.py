import os
from dotenv import load_dotenv

load_dotenv()


def get_int_env_variable(var_name, default=None):

    value = os.getenv(var_name, default)
    if value is not None:
        try:
            return int(value)
        except ValueError:
            raise ValueError(
                f"Environment variable '{var_name}' must be an integer. Got '{value}' instead."
            )
    return default


# Configuration
ANKI_CONNECT_URL = "http://localhost:8765"
MEDIA_DIR = os.getenv("MEDIA_DIR")
AUDIO_FILE_PATTERN = r"^(.+?)_random(?:_\d+)?\.mp3$"
MODEL_NAME = os.getenv("MODEL_NAME", "Basic")
SEARCH_FIELD = os.getenv("SEARCH_FIELD", "Word")
TARGET_FIELD = os.getenv("TARGET_FIELD", "ForvoPronunciations")

FORVO_LANGUAGE = os.getenv("FORVO_LANGUAGE", "en")  # Default to English
FORVO_API_KEY = os.getenv("FORVO_API_KEY")


DEFAULT_QUERY = os.getenv(
    "ANKI_SEARCH_QUERY", "-tag:preposition"
)  # Default query if none provided

# Forvo API limit
DAILY_REQUEST_LIMIT = get_int_env_variable(
    "DAILY_REQUEST_LIMIT", 500
)  # Adjust based on Forvo's rate limits
# Number of days after which a failed attempt to find in Forvo
# can be retried.
RETRY_AFTER_DAYS = get_int_env_variable("RETRY_AFTER_DAYS", 30)

## Cache & Backup
BACKUP_DIR = os.getenv("BACKUP_DIR")
CACHE_FILE = os.getenv("CACHE_FILE", "cache.json")  # File to store cached data
# Keep backup cache for this many days
BACKUP_KEEP_DAYS = get_int_env_variable("BACKUP_KEEP_DAYS", 30)
