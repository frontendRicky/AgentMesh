# Smoke Commands

These commands provide a quick release candidate sanity check. Use a sandbox `--project-root` when possible.

| Command | Writes files? | Notes |
|---|---:|---|
| `python3.11 -m a2a_runtime.cli --project-root . --help` | No | Prints CLI help and safety notes. |
| `python3.11 -m a2a_runtime.cli --project-root . task list` | No | Lists task workspaces. |
| `python3.11 -m a2a_runtime.cli --project-root . task active` | No | Prints active task id. |
| `python3.11 -m a2a_runtime.cli --project-root . status` | No | Prints active task status. |
| `python3.11 -m a2a_runtime.cli --project-root . validate` | No | Runs read-only validation checks. |
| `python3.11 -m a2a_runtime.cli --project-root . prompt controller` | No | Prints Controller prompt. |
| `python3.11 -m a2a_runtime.cli --project-root . report` | No | Prints runtime report to stdout. |

## Minimal Write Smoke

Use this only in a temporary project root:

```bash
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-smoke task create --type feature --title "Smoke task" --priority P1 --owner zhangxia --yes
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-smoke status
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-smoke prompt pm
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-smoke prompt architect
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-smoke validate identity
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-smoke report
python3.11 -m a2a_runtime.cli --project-root /tmp/a2a-smoke gate developer --path src/pages/settings/index.tsx --operation modify
```

The smoke flow does not create business source files and does not call a real LLM.
