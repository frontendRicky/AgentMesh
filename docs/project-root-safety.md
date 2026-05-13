# Project Root Safety

The CLI resolves every path from `--project-root`.

Default validation rejects sensitive roots and their child paths:

- `/`
- `/etc`
- `/usr`
- `/var`
- `/private`
- `/System`
- `/Library`
- `~/Library`

Examples such as `/etc/foo`, `/usr/local/foo`, `/var/tmp/foo`, and `/private/tmp/foo` are rejected even if they contain project markers.

A project root must contain at least one marker:

- `.ai-agents/`
- `.git/`
- `pyproject.toml`
- `package.json`

`--allow-non-project-root` is reserved for tests and emits a warning. It must not be used to point Runtime at system directories.

`task create` prints the resolved project root, project markers, existing task count, and planned task id before writing.

Forbidden source/control paths inside a safe project root are handled separately by Developer Gate. See `docs/forbidden-paths.md`.
