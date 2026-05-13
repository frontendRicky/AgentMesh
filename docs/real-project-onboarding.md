# Real Project Onboarding

This guide describes how to use the Python A2A Runtime in an existing project.

## Prerequisites

- Python 3.11+.
- The project already has `.ai-agents/**`.
- Markdown A2A v1.0.0 is frozen for the project.
- The Runtime is available in the project checkout.
- The Runtime does not automatically write business source code.

## First Use

Start with read-only commands:

```bash
python3.11 -m a2a_runtime.cli --project-root . status
python3.11 -m a2a_runtime.cli --project-root . validate
python3.11 -m a2a_runtime.cli --project-root . task list
```

Create a task only after confirming the target project root:

```bash
python3.11 -m a2a_runtime.cli --project-root . task create --type feature --title "xxx" --priority P1 --owner <you> --yes
python3.11 -m a2a_runtime.cli --project-root . prompt pm
```

## Working With Cursor

The Runtime generates prompts and validates Runtime state. Cursor performs actual agent work.

1. Runtime generates a prompt.
2. User reviews and copies the prompt to Cursor.
3. Cursor performs the requested agent work and writes allowed A2A artifacts or, for Developer, business source edits.
4. Runtime validates state, gates, reviews, blockers, risks, and final delivery.

Example prompt flow:

```bash
python3.11 -m a2a_runtime.cli --project-root . prompt pm
python3.11 -m a2a_runtime.cli --project-root . prompt architect
python3.11 -m a2a_runtime.cli --project-root . review approve --stage architect --step 1 --reviewer <you> --yes
python3.11 -m a2a_runtime.cli --project-root . review approve --stage architect --step 2 --reviewer <you> --yes
python3.11 -m a2a_runtime.cli --project-root . prompt developer --path src/pages/settings/index.tsx --operation modify
python3.11 -m a2a_runtime.cli --project-root . gate developer --path src/pages/settings/index.tsx --operation modify
```

## Safety Boundaries

- Runtime does not directly modify business source code.
- Developer source edits are still performed by Cursor.
- Developer edits must pass GateService and file-change-plan checks.
- P0/P1 risks must pass Human Risk Decision Gate.
- Human Review and Final Review must use the double-step flow.
- Formal blockers must use the two-stage blocker mechanism.

## Recommended First Real Project Routine

1. Run `status`, `validate`, and `report`.
2. Create a low-risk task with `task create`.
3. Generate `prompt pm` and `prompt architect`.
4. Keep Developer prompts readonly until Architect review is approved.
5. Use `gate developer` before any Developer source edit.
6. Use `report --output archive/runtime-report.md --yes` after each milestone.

## Pilot Checklist

For a staged pilot plan, see `docs/real-project-pilot-checklist.md`.

## Release Candidate Warning

Do not run `git tag`, `git commit`, or `git push` as part of the Runtime pilot. The Runtime does not perform git integration; release tagging is a separate human release action.
