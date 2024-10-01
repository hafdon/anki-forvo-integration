import shutil
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
CACHE_FILE = os.getenv("CACHE_FILE")
BACKUP_DIR = os.getenv("BACKUP_DIR")
BACKUP_KEEP_DAYS = os.getenv("BACKUP_KEEP_DAYS")

from fetch_forvo_pronunciations import main as forvo_main


def backup_keep_days():
    # Convert to an integer if the value exists
    if BACKUP_KEEP_DAYS is not None:
        value_int = int(BACKUP_KEEP_DAYS)
    else:
        print("BACKUP_KEEP_DAYS is not set. Using 31")
    return value_int or 31


def limit_backups():
    # Delete backups older than 30 days
    days_to_keep = backup_keep_days()
    now = datetime.now()

    for filename in os.listdir(BACKUP_DIR):
        # Construct full file path
        file_path = os.path.join(BACKUP_DIR, filename)

        # Check if the file is a file (and not a directory)
        if os.path.isfile(file_path):
            # Get the last modification time of the file
            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))

            # If the file is older than `days_to_keep`, delete it
            if now - file_mtime > timedelta(days=days_to_keep):
                os.remove(file_path)
                print(f"Deleted old backup: {file_path}")


def backup_cache():
    # Create a timestamp for versioning the backup
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Make sure the backup directory exists
    os.makedirs(BACKUP_DIR, exist_ok=True)

    # Define the destination file name with a timestamp for version control
    backup_file = os.path.join(BACKUP_DIR, f"cache_backup_{timestamp}.json")

    # Copy the file from the source to the backup destination
    shutil.copy2(CACHE_FILE, backup_file)

    print(f"Backup successful: {backup_file}")


def main():

    print("Logging to log file.")

    limit_backups()
    backup_cache()
    forvo_main()

    print("Check log file for details.")


if __name__ == "__main__":
    main()
