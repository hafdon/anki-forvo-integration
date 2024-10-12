# Modules Overview

## 1. `factories.py`

### Purpose

Implements the Factory Pattern to manage the creation of various manager instances used throughout the application.

### Classes

- **ManagerFactory**
  - **Methods**:
    - `create_backup_manager()`: Returns an instance of `BackupManager`.
    - `create_cache_manager()`: Returns an instance of `CacheManager`.
    - `create_forvo_manager()`: Returns an instance of `ForvoManager`.
    - `create_anki_note_manager()`: Returns an instance of `AnkiNoteManager`.
    - `create_anki_file_manager()`: Returns an instance of `AnkiFileManager`.

## 2. `singleton.py`

### Purpose

Defines a thread-safe Singleton metaclass to ensure that certain managers have only one instance throughout the application's lifecycle.

### Classes

- **SingletonMeta**
  - **Description**: A metaclass that enforces the Singleton pattern, ensuring a class has only one instance.

## 3. `commands.py`

### Purpose

Implements the Command Pattern to encapsulate the actions performed on each word, promoting modularity and extensibility.

### Classes

- **WordProcessingCommand**
  - **Attributes**:
    - `word`: The word to process.
    - `forvo_manager`: Instance of `ForvoManager`.
    - `anki_note_manager`: Instance of `AnkiNoteManager`.
    - `anki_file_manager`: Instance of `AnkiFileManager`.
    - `cache_manager`: Instance of `CacheManager`.
    - `logger`: Logger instance for logging activities.
  - **Methods**:
    - `execute()`: Executes the command to fetch pronunciations, update Anki notes, and manage cache.

## 4. `application.py`

### Purpose

Serves as the core application class, managing the workflow from argument parsing to executing commands.

### Classes

- **Application**
  - **Attributes**:
    - `backup_manager`: Instance of `BackupManager`.
    - `cache_manager`: Instance of `CacheManager`.
    - `forvo_manager`: Instance of `ForvoManager`.
    - `anki_note_card_manager`: Instance of `AnkiNoteManager`.
    - `anki_file_manager`: Instance of `AnkiFileManager`.
    - `search_query`: Parsed search query argument.
    - `retry_after_days`: Parsed retry-after-days argument.
  - **Methods**:
    - `__init__(args=None)`: Initializes the application with dependencies and parsed arguments.
    - `parse_args(args)`: Parses command-line arguments.
    - `setup()`: Performs initial setup tasks like backups and cache resets.
    - `run()`: Executes the main application workflow.
