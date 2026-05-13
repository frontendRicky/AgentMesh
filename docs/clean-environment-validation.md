# Clean Environment Validation

Use this guide to verify the Release Candidate in a clean shell without installing extra dependencies.

## Requirements

- Python 3.11+
- No additional Python dependencies
- No `click`, `typer`, `rich`, `pydantic`, or pytest requirement
- No real LLM credentials
- No git repository requirement

## Run Without Installing

From the Runtime checkout:

```bash
python3.11 -m a2a_runtime.cli --help
python3.11 -m a2a_runtime.cli --project-root . --json status
```

The `pyproject.toml` entry point is available only after package installation:

```toml
[project.scripts]
a2a-agent = "a2a_runtime.cli:main"
```

Tests should continue to use module execution and must not require installation:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/a2a_runtime_pycache python3.11 -m compileall a2a_runtime tests
PYTHONPYCACHEPREFIX=/private/tmp/a2a_runtime_pycache python3.11 -m unittest discover -s tests
```

## Optional Installed Entry Point Check

If a human chooses to install the package in a temporary virtual environment, verify:

```bash
a2a-agent --help
a2a-agent --project-root . --json status
```

Do not install dependencies, do not run git commands, and do not use a real LLM provider for this validation.

## Expected Result

- Help text renders.
- Tests pass.
- No business source files are created.
- No `.cursor` files are created.
- No `.ai-agents` protocol files are modified.
