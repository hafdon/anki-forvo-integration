# Contribution Guidelines

Thank you for considering contributing to the **Anki Forvo Pronunciation Updater**! Your contributions help improve the project for everyone. Please follow the guidelines below to ensure a smooth collaboration process.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Reporting Issues](#reporting-issues)
- [Submitting Pull Requests](#submitting-pull-requests)
- [Coding Standards](#coding-standards)
- [Testing](#testing)

## Code of Conduct

Please adhere to our [Code of Conduct](CODE_OF_CONDUCT.md) to ensure a welcoming and respectful environment for all contributors.

## How to Contribute

1. **Fork the Repository**

   Click the "Fork" button at the top-right corner of the repository page to create your own copy.

2. **Clone Your Fork**

   ```bash
   git clone https://github.com/yourusername/anki-forvo-updater.git
   cd anki-forvo-updater
   ```

3. **Set Up the Development Environment**

   Follow the [Setup and Installation Guide](setup.md) to set up your environment.

4. **Create a New Branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

5. **Make Your Changes**

   Implement your feature or bug fix. Ensure your code follows the project's coding standards.

6. **Run Tests**

   Ensure all tests pass before committing your changes.

7. **Commit Your Changes**

   ```bash
   git add .
   git commit -m "Add feature: your feature description"
   ```

8. **Push to Your Fork**

   ```bash
   git push origin feature/your-feature-name
   ```

9. **Create a Pull Request**

   Navigate to the original repository and click "Compare & pull request". Provide a clear description of your changes.

## Reporting Issues

If you encounter any bugs or have suggestions for improvements, please open an issue in the repository's [Issues](https://github.com/yourusername/anki-forvo-updater/issues) section.

**When reporting an issue, please include:**

- A clear and descriptive title.
- A detailed description of the problem.
- Steps to reproduce the issue.
- Expected vs. actual behavior.
- Any relevant logs or screenshots.

## Submitting Pull Requests

Follow these steps to submit a pull request:

1. Ensure your fork is up to date with the main repository.
2. Follow the [How to Contribute](#how-to-contribute) steps.
3. Provide a clear and descriptive title and description for your pull request.
4. Reference any related issues by using keywords like `Closes #issue-number`.
5. Ensure all tests pass and your code adheres to the project's standards.

## Coding Standards

- **Language**: Python 3.8+
- **Style Guide**: Follow [PEP 8](https://pep8.org/) for code styling.
- **Docstrings**: Use [Google style](https://www.python.org/dev/peps/pep-0257/) for docstrings.
- **Naming Conventions**:
  - Classes: `CamelCase`
  - Functions and Variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`

## Testing

Ensure that your contributions include appropriate tests. Follow the existing testing structure and add new tests as needed.

- **Run Tests**:

  ```bash
  python -m unittest discover tests
  ```

- **Writing Tests**:

  Place your test files in the `tests/` directory, following the naming convention `test_module.py`.

---

Thank you for your interest in contributing to **Anki Forvo Pronunciation Updater**! We appreciate your support and look forward to your contributions.
