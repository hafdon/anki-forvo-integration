# factories.py
from anki.anki_note_manager import AnkiNoteManager
from anki.anki_file_manager import AnkiFileManager
from backup.backup_manager import BackupManager
from cache.cache_manager import CacheManager
from config.config import ANKI_CONNECT_URL, CACHE_FILE
from forvo.forvo_manager import ForvoManager


class ManagerFactory:
    @staticmethod
    def create_backup_manager():
        return BackupManager()

    @staticmethod
    def create_cache_manager():
        return CacheManager(CACHE_FILE, 500, 30)

    @staticmethod
    def create_forvo_manager():
        return ForvoManager()

    @staticmethod
    def create_anki_note_card_manager():
        return AnkiNoteManager(ANKI_CONNECT_URL)

    @staticmethod
    def create_anki_file_manager():
        return AnkiFileManager(ANKI_CONNECT_URL)
