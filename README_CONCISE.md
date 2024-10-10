# Anki Forvo Pronunciation Updater

## Introduction

The **Anki Forvo Pronunciation Updater** is a tool designed to fetch pronunciations from Forvo and update Anki notes based on a specified search query. It ensures that Anki flashcards are enriched with accurate pronunciations, enhancing the language learning experience.

## Features

- **Pronunciation Fetching**: Retrieves pronunciations from Forvo.
- **Anki Integration**: Updates Anki notes with fetched pronunciations.
- **Caching Mechanism**: Caches requests to minimize redundant API calls.
- **Backup Management**: Maintains backups of cache and configurations.
- **Robust Logging**: Detailed logging for monitoring and debugging.
- **Configurable Parameters**: Customize search queries and retry mechanisms.

## Architecture Overview

The system employs several design patterns, including Factory, Singleton, and Command patterns, to ensure a modular, scalable, and maintainable codebase. For a detailed architecture description, refer to the [Architecture Documentation](docs/architecture.md).

## Getting Started

- [Setup and Installation](docs/setup.md)
- [Usage Instructions](docs/usage.md)

## Contributing

Contributions are welcome! Please see the [Contribution Guidelines](docs/contribution.md) for more details.

## License

This project is licensed under the MIT License.
