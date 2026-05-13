# Real Project Pilot Checklist

Use this checklist for the first controlled pilot in a real project. In `0.1.0rc5`, Stage 0 / Stage 1 / Stage 2 can proceed. Stage 3 / Stage 4 should remain under explicit human supervision. Keep each stage small and stop if any safety gate fails.

## Stage 0: Read-only Validation

Run only read-only commands:

```bash
python3.11 -m a2a_runtime.cli --project-root . status
python3.11 -m a2a_runtime.cli --project-root . validate
python3.11 -m a2a_runtime.cli --project-root . task list
python3.11 -m a2a_runtime.cli --project-root . task active
python3.11 -m a2a_runtime.cli --project-root . report
```

Confirm:

- Project root is correct.
- Active task resolution is understood.
- No business source files are written.
- No `.cursor` files are written.
- No real LLM API is called.

## Stage 1: Create Task, But Do Not Modify Source

Preview first:

```bash
python3.11 -m a2a_runtime.cli --project-root . task create --type feature --title "Pilot task" --priority P1 --owner <you> --dry-run
```

Create after review:

```bash
python3.11 -m a2a_runtime.cli --project-root . task create --type feature --title "Pilot task" --priority P1 --owner <you> --yes
python3.11 -m a2a_runtime.cli --project-root . prompt pm
python3.11 -m a2a_runtime.cli --project-root . prompt architect
```

Confirm Runtime created only task workspace files and did not enter source modification.

## Stage 2: Human Review + Developer Gate Dry-run

After PM and Architect artifacts are prepared and reviewed:

```bash
python3.11 -m a2a_runtime.cli --project-root . review approve --stage architect --step 1 --reviewer <you> --yes
python3.11 -m a2a_runtime.cli --project-root . review approve --stage architect --step 2 --reviewer <you> --yes
python3.11 -m a2a_runtime.cli --project-root . prompt developer --path src/pages/settings/index.tsx --operation modify
python3.11 -m a2a_runtime.cli --project-root . gate developer --path src/pages/settings/index.tsx --operation modify
```

Confirm:

- Architect review record exists.
- State is `developer_processing`.
- Developer Gate dry-run returns the expected decision.
- If GateService returns `blocker_request` or `risk_decision_required`, stop and use the appropriate Runtime flow.

## Stage 3: Allow Cursor Execution, Runtime Still Does Not Write Source

The Runtime prints prompts only. The user manually copies the Developer prompt to Cursor.

Pilot rules:

- Cursor performs the Developer work.
- Runtime does not directly write business source.
- Cursor must follow A2A gates and file-change-plan.
- Runtime is used only for `gate`, `report`, `validate`, blocker, review, and risk flows.

Suggested validation loop:

```bash
python3.11 -m a2a_runtime.cli --project-root . gate developer --path src/pages/settings/index.tsx --operation modify
python3.11 -m a2a_runtime.cli --project-root . validate
python3.11 -m a2a_runtime.cli --project-root . report
```

## Stage 4: QA + Final Review

After Developer artifacts and QA artifacts are present:

```bash
python3.11 -m a2a_runtime.cli --project-root . prompt qa
python3.11 -m a2a_runtime.cli --project-root . review approve --stage final --step 1 --reviewer <you> --yes
python3.11 -m a2a_runtime.cli --project-root . review approve --stage final --step 2 --reviewer <you> --yes
python3.11 -m a2a_runtime.cli --project-root . finalize --yes
python3.11 -m a2a_runtime.cli --project-root . report --output archive/runtime-report.md --yes
```

Confirm:

- Finalize fails if unresolved P0/P1 risks exist.
- Finalize fails if an active blocker exists.
- Final delivery references upstream artifacts and reviews.
- Report export writes only to task archive.

## Pilot Stop Conditions

- Runtime appears to write business source.
- Runtime appears to modify `.cursor`.
- Runtime appears to modify `.ai-agents` protocol structure.
- GateService is not respected.
- Human Review is skipped.
- P0/P1 risk is accepted without explicit human decision.
- Any command suggests git tag, commit, push, or MR creation as an automatic Runtime action.
