import os
import argparse

from backup_manager import BackupManager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# from fetch_forvo_pronunciations import main as forvo_main

RETRY_AFTER_DAYS = 30
DEFAULT_QUERY = os.getenv(
    "ANKI_SEARCH_QUERY", 'deck:"Default"'
)  # Default query if none provided


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

    print("Logging to log file.")
    backup = BackupManager()

    backup.limit_backups()
    backup.backup_cache()

    # Parse command-line arguments for the search query and retry configuration
    search_query, retry_after_days = parse_local_args()
    print(search_query, retry_after_days)

    # forvo_main()

    print("Check log file for details.")


if __name__ == "__main__":
    main()
