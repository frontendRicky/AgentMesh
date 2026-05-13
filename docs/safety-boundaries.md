# Safety Boundaries

The Python A2A Runtime is a local Markdown file runtime. It coordinates A2A task state and validates gates. It is not an autonomous coding agent.

## Runtime Does Not

- Does not automatically modify business source code.
- Does not call a real LLM.
- Does not automatically execute Cursor Prompt.
- Does not commit.
- Does not push.
- Does not create MR.
- Does not modify `.ai-agents` protocol structure.
- Does not modify `.cursor`.
- Does not bypass review.
- Does not bypass GateService.
- Does not accept P0/P1 risk automatically.

## Writable Paths

The Runtime may write only these task-scoped paths:

- `workspace/<task-id>/task.md`
- `workspace/<task-id>/state.md`
- `workspace/<task-id>/messages/**`
- `workspace/<task-id>/blockers/**`
- `workspace/<task-id>/human-reviews/**`
- `workspace/<task-id>/artifacts/final/**`
- `workspace/<task-id>/archive/**`
- `workspace/active-task.md`

## Commands That Write

- `task create`
- `task use`
- `review approve`
- `review reject`
- `blocker request`
- `blocker create`
- `blocker resolve`
- `risk decide`
- `finalize`
- `report --output archive/...`

All mutating commands require `--yes` for actual writes and support `--dry-run` where applicable.

## Business Source Boundary

Developer changes to business source are performed by Cursor, not by this Runtime. Before a Developer edit, run:

```bash
python3.11 -m a2a_runtime.cli --project-root . gate developer --path <path> --operation <create|modify|delete>
```

If GateService does not allow the change, do not proceed with the source edit. Use blocker or risk flows instead.

## Final Delivery Boundary

Final delivery is allowed only when FinalDeliveryService gates pass:

- final review approved
- current status completed
- current agent controller
- no active blocker
- no blocked context
- required upstream artifacts exist and are ready
- test report has no unresolved fail
- no unresolved P0/P1 risk
