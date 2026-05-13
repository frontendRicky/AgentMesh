# CLI Exit Codes

- `0`: success
- `1`: validation failed
- `2`: user decision required / unresolved blocking risk
- `3`: task not found or active task missing
- `4`: invalid command arguments
- `5`: internal error

All commands support `--project-root` and `--json`.

Mutating commands require `--yes` to write and support `--dry-run` where applicable.

The CLI does not modify business source code, does not call a real LLM, and does not automatically execute Cursor prompts.

Warnings do not change exit code. For example, `risk decide --by` may succeed with exit code `0` while emitting a local-user mismatch warning in text and JSON output.

`finalize` returns exit code `2` when unresolved `P0_BLOCKER`, `P1_HIGH`, or `P2_MEDIUM + requires_human_decision` risks block final delivery.
