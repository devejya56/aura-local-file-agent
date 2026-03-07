# 🤝 Contributing to Aura

First off, thank you for considering contributing to Aura! It's people like you that make Aura such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* **Use a clear and descriptive title**
* **Describe the exact steps which reproduce the problem**
* **Provide specific examples to demonstrate the steps**
* **Describe the behavior you observed after following the steps**
* **Explain which behavior you expected to see instead and why**
* **Include screenshots and animated GIFs if possible**
* **Include your environment details** (OS, Python version, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* **Use a clear and descriptive title**
* **Provide a step-by-step description of the suggested enhancement**
* **Provide specific examples to demonstrate the steps**
* **Describe the current behavior and expected behavior**
* **Explain why this enhancement would be useful**

## Pull Request Process

1. **Fork the repository** and create your branch from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** with clear, descriptive commit messages
   ```bash
   git commit -m "type: brief description of changes"
   ```

3. **Write or update tests** if applicable

4. **Update documentation** including README.md if needed

5. **Push to your fork** and create a Pull Request to the `main` branch
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Link related issues** in your PR description

7. **Ensure all CI checks pass** before requesting review

8. **Request review** from maintainers

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/aura-local-file-agent.git
   cd aura-local-file-agent
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate      # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature
   ```

5. **Make your changes and test thoroughly**

6. **Push and create a Pull Request**

## Coding Standards

* Use **PEP 8** style guide for Python code
* Write **docstrings** for all functions and classes
* Add **type hints** where applicable
* Keep functions **small and focused**
* Write **clear variable names**
* Add **comments** for complex logic

## Commit Message Guidelines

We follow conventional commits:

```
type(scope): subject

body

footer
```

**Types:**
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Test additions or changes
- `chore`: Build process, dependencies, etc.

**Examples:**
```
feat(agent): add support for image classification
fix(database): resolve undo history corruption
docs(readme): update installation instructions
```

## Testing

* Write tests for new features
* Ensure all existing tests pass
* Run tests locally before submitting PR:
  ```bash
  pytest tests/
  ```

## Documentation

* Update README.md if you change functionality
* Add docstrings to all public functions
* Update SETUP.md if installation/configuration changes
* Include code examples for new features

## Questions?

Feel free to open an issue or discussion for questions about contributing!

---

**Thank you for contributing to Aura! 🚀**
