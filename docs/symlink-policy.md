# Symlink Policy

Runtime rejects report export paths that could escape the task archive through symlinks.

Rules:

- `report --output` must be a relative path.
- The output must start with `archive/`.
- The resolved output must stay inside `workspace/<task-id>/archive/**`.
- `archive/` must not be a symlink.
- Any existing output parent directory must not be a symlink.
- `--dry-run` uses the same validation as `--yes`.

Runtime does not implement external report output in V1.

