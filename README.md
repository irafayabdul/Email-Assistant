# Email-Assistant

## 🚀 Getting Started

This document will guide you through setting up your development environment for the Email-Assistant project.

### 📦 Dependency Management with Poetry

This project uses **Poetry** for dependency management and packaging. Poetry ensures that you have a consistent and reproducible development environment. The dependencies are defined in the `pyproject.toml` file and locked in the `poetry.lock` file.

To install the project dependencies, you need to have Poetry installed. Then, run the following command in the root of the project:

```bash
poetry install
```

For tox testing but avoiding conflict with dev dependencies, run the following command:
```bash
 pip install pipx
 pipx ensurepath
 pipx install tox
```

This will create a virtual environment inside the project's root directory and install all the necessary dependencies.

### ✅ Code Quality with Pre-commit Hooks

We use **pre-commit** hooks to ensure code quality and consistency before any code is committed. The hooks are configured in the `.pre-commit-config.yaml` file and include:

  * **`black`**: An opinionated code formatter.
  * **`flake8`**: A tool to check for style and quality issues.
  * **`reorder-python-imports`**: A tool to automatically sort imports.
  * **`mypy`**: A static type checker.

To set up the pre-commit hooks, run the following command after installing the dependencies:

```bash
pre-commit install
```

Now, the hooks will run automatically every time you make a commit.

### 🧪 Testing with Tox

We use **Tox** to automate and standardize testing in isolated environments. The `tox.ini` file is configured to run the following checks:

  * **`lint`**: Runs all pre-commit hooks to check for code quality.
  * **`mypy`**: Runs the static type checker.

To run all the checks, simply execute the following command:

```bash
tox
```
