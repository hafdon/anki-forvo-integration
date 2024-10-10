# Design Patterns Utilized

This project employs several design patterns to enhance modularity, scalability, and maintainability. Below is an overview of each pattern used and its application within the system.

## 1. Factory Pattern

### Purpose

The Factory Pattern centralizes the creation of objects, allowing for greater flexibility and decoupling between object creation and usage.

### Implementation

- **Module**: `factories.py`
- **Classes Involved**: `ManagerFactory`

### Benefits

- **Decoupling**: Separates object creation from business logic.
- **Flexibility**: Easily switch out or modify manager implementations without affecting dependent code.
- **Maintainability**: Centralizes instantiation logic, making it easier to manage dependencies.

## 2. Singleton Pattern

### Purpose

Ensures that a class has only one instance and provides a global point of access to it.

### Implementation

- **Module**: `singleton.py`
- **Classes Involved**: `SingletonMeta`

### Usage

Applied to managers like `CacheManager` and `BackupManager` to prevent multiple instances that could lead to inconsistent states or redundant operations.

### Benefits

- **Resource Management**: Prevents unnecessary allocation of resources.
- **Consistency**: Ensures a single source of truth for shared resources.

## 3. Command Pattern

### Purpose

Encapsulates a request as an object, thereby allowing for parameterization of clients with queues, requests, and operations.

### Implementation

- **Module**: `commands.py`
- **Classes Involved**: `WordProcessingCommand`

### Usage

Each `WordProcessingCommand` object represents the operations needed to process a single word, including fetching pronunciations, updating Anki notes, and managing cache.

### Benefits

- **Modularity**: Isolates the execution logic for processing words.
- **Extensibility**: Facilitates the addition of new commands without altering existing code.
- **Reusability**: Commands can be reused in different contexts or workflows.

## 4. Dependency Injection

### Purpose

Decouples the creation of a component's dependencies from the component itself, allowing for more flexible and testable code.

### Implementation

- **Module**: `application.py`
- **Usage**: Dependencies like `BackupManager`, `CacheManager`, `ForvoManager`, `AnkiNoteManager`, and `AnkiFileManager` are injected into the `Application` class via the `ManagerFactory`.

### Benefits

- **Testability**: Allows for easy mocking of dependencies during testing.
- **Flexibility**: Facilitates swapping out implementations without modifying dependent classes.
- **Maintainability**: Enhances code readability by clearly defining dependencies.

## 5. Singleton and Factory Patterns Combined

### Purpose

While the Factory Pattern handles object creation, the Singleton Pattern ensures that only one instance of each manager is created, even when requested multiple times via the factory.

### Implementation

- **Interaction**: `ManagerFactory` utilizes the Singleton behavior of managers like `CacheManager` and `BackupManager` to always return the same instance.

### Benefits

- **Consistency**: Guarantees that shared resources are accessed through a single instance.
- **Efficiency**: Reduces overhead by preventing multiple instances of resource-heavy managers.
