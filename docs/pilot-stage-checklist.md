# Pilot Stage Checklist

## Stage 0: Read-only Validation

- `status`
- `validate`
- `task list`
- `task active`
- `report`

## Stage 1: Create Task Without Source Changes

- `task create --dry-run`
- `task create --yes`
- `prompt pm`
- `prompt architect`
- `model recommend`

## Stage 2: Human Review + Developer Gate Dry-run

- `review approve --stage architect --step 1`
- `review approve --stage architect --step 2`
- `prompt developer --path ... --operation modify`
- `gate developer --path ... --operation modify`

## Stage 3: Cursor Execution Under Supervision

- Copy the Developer prompt to Cursor manually.
- Cursor may write business source only after GateService allows the target path.
- Runtime does not write business source directly.

## Stage 4: QA + Final Review Under Supervision

- `prompt qa`
- `review approve --stage final --step 1`
- `review approve --stage final --step 2`
- `finalize --dry-run`
- `finalize --yes`
- `report --output archive/runtime-report.md --yes`

Stage 0 / 1 / 2 are ready for real-project Pilot in `0.1.0rc5`, including monorepo CI path blocking in Developer Gate. Stage 3 / 4 should remain supervised.
